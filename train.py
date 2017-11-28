#!/usr/bin/env python
__author__ = 'solivr'

import argparse
import os
import csv
import numpy as np
from tqdm import trange
import tensorflow as tf
from src.model import crnn_fn
from src.data_handler import data_loader
from src.data_handler import preprocess_image_for_prediction

from src.config import Params, Alphabet, import_params_from_json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ft', '--csv_files_train', required=True, type=str, help='CSV filename for training',
                        nargs='*', default=None)
    parser.add_argument('-fe', '--csv_files_eval', type=str, help='CSV filename for evaluation',
                        nargs='*', default=None)
    parser.add_argument('-o', '--output_model_dir', required=True, type=str,
                        help='Directory for output', default='./estimator')
    parser.add_argument('-n', '--nb-epochs', type=int, default=30, help='Number of epochs')
    parser.add_argument('-g', '--gpu', type=str, help="GPU 0,1 or '' ", default='')
    parser.add_argument('-p', '--params-file', type=str, help='Parameters filename', default=None)
    args = vars(parser.parse_args())

    if args.get('params_file'):
        dict_params = import_params_from_json(json_filename=args.get('params_file'))
        parameters = Params(**dict_params)
    else:
        parameters = Params(train_batch_size=128,
                            eval_batch_size=128,
                            learning_rate=1e-3,  # 1e-3 recommended
                            learning_decay_rate=0.95,
                            learning_decay_steps=5000,
                            evaluate_every_epoch=5,
                            save_interval=5e3,
                            input_shape=(128, 1792),
                            optimizer='adam',
                            digits_only=False,
                            alphabet=Alphabet.LETTERS_DIGITS_EXTENDED,
                            alphabet_decoding='same',
                            csv_delimiter=' ',
                            csv_files_eval=args.get('csv_files_eval'),
                            csv_files_train=args.get('csv_files_train'),
                            output_model_dir=args.get('output_model_dir'),
                            n_epochs=args.get('nb_epochs'),
                            gpu=args.get('gpu')
                            )

    model_params = {
        'Params': parameters,
    }

    parameters.export_experiment_params()

    os.environ['CUDA_VISIBLE_DEVICES'] = parameters.gpu
    config_sess = tf.ConfigProto()
    config_sess.gpu_options.per_process_gpu_memory_fraction = 0.8
    config_sess.gpu_options.allow_growth = True

    # Config estimator
    est_config = tf.estimator.RunConfig()
    est_config.replace(keep_checkpoint_max=10,
                       save_checkpoints_steps=parameters.save_interval,
                       session_config=config_sess,
                       save_checkpoints_secs=None,
                       save_summary_steps=1000,
                       model_dir=parameters.output_model_dir)

    estimator = tf.estimator.Estimator(model_fn=crnn_fn,
                                       params=model_params,
                                       model_dir=parameters.output_model_dir,
                                       config=est_config
                                       )

    # Count number of image filenames in csv
    n_samples = 0
    for file in parameters.csv_files_eval:
        with open(file, 'r', encoding='utf8') as csv_file:
            reader = csv.reader(csv_file, delimiter=parameters.csv_delimiter)
            n_samples += len(list(reader))

    try:
        for e in trange(0, parameters.n_epochs, parameters.evaluate_every_epoch):
            estimator.train(input_fn=data_loader(csv_filename=parameters.csv_files_train,
                                                 params=parameters,
                                                 batch_size=parameters.train_batch_size,
                                                 num_epochs=parameters.evaluate_every_epoch,
                                                 data_augmentation=True,
                                                 image_summaries=True))
            estimator.evaluate(input_fn=data_loader(csv_filename=parameters.csv_files_eval,
                                                    params=parameters,
                                                    batch_size=parameters.eval_batch_size,
                                                    num_epochs=1),
                               steps=np.floor(n_samples/parameters.eval_batch_size)
                               )

    except KeyboardInterrupt:
        print('Interrupted')
        estimator.export_savedmodel(os.path.join(parameters.output_model_dir, 'export'),
                                    preprocess_image_for_prediction(min_width=10))
        print('Exported model to {}'.format(os.path.join(parameters.output_model_dir, 'export')))

    estimator.export_savedmodel(os.path.join(parameters.output_model_dir, 'export'),
                                preprocess_image_for_prediction(min_width=10))
    print('Exported model to {}'.format(os.path.join(parameters.output_model_dir, 'export')))
