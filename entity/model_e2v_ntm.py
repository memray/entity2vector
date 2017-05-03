# plain entity 2 vec model
import os
from keras.models import Model
from keras.layers import Input
from keras.layers import Merge
from keras.layers.merge import dot, concatenate, Dot, Concatenate
from keras.layers.core import *
from keras.layers.embeddings import *
from entity.model.layers import *
from entity.data import DataProvider
from keras.callbacks import ModelCheckpoint
from entity.model.callbacks import *
import numpy as np
from entity.config import Config
from keras.optimizers import *
import numpy as np
import sys
import tensorflow as tf

# log setting
#import sys
#sys.stdout = open(conf.path_log, "w")

def build_ntm_model(conf, dp):
    n_terms = len(dp.idx2word)
    word_embed_data = np.array(dp.word_embed)

    item_embed_data = np.random.rand(dp.get_item_size(), conf.dim_item)
    word_transfer_W = np.random.rand(conf.dim_word, conf.dim_item)
    word_transfer_b = np.random.rand(conf.dim_item)
    print("finish data processing")

    # define model
    word_input = Input(shape=(1,), dtype ="int32", name ="word_idx")
    item_pos_input = Input(shape=(1,), dtype ="int32", name ="item_pos_idx")
    item_neg_input = Input(shape=(1,), dtype ="int32", name ="item_neg_idx")

    word_embed = Embedding(output_dim=conf.dim_word, input_dim=n_terms, input_length=1, name="word_embed",
                           weights=[word_embed_data], trainable=False)
    item_embed = Embedding(output_dim=conf.dim_item, input_dim=dp.get_item_size(), input_length=1, name="item_embed",
                           weights=[item_embed_data], trainable=True)

    word_embed_ = word_embed(word_input)
    item_pos_embed_ = item_embed(item_pos_input)
    item_neg_embed_ = item_embed(item_neg_input)

    # word_flatten = Flatten()
    word_embed_ = Flatten()(word_embed_)
    word_embed_ = Dense(activation="sigmoid", output_dim=conf.dim_item, input_dim=conf.dim_word, trainable=True,
                        weights=[word_transfer_W, word_transfer_b], name="word_transfer")(word_embed_)

    item_pos_embed_ = Reshape((conf.dim_item,))(Flatten()(item_pos_embed_))
    item_neg_embed_ = Reshape((conf.dim_item,))(Flatten()(item_neg_embed_))
    item_pos_embed_ = Activation(activation="softmax", name="item_pos_act")(item_pos_embed_)
    item_neg_embed_ = Activation(activation="softmax", name="item_neg_act")(item_neg_embed_)

    # pos_layer = Merge(mode="dot", dot_axes=-1, name="pos_layer")
    # pos_layer_ = pos_layer([word_embed_, item_pos_embed_])
    # pos_layer_ = dot([word_embed_, item_pos_embed_], axes=-1, normalize=False, name="pos_layer")
    pos_layer_ = Dot(axes=-1, normalize=False, name="pos_layer")([word_embed_, item_pos_embed_])
    # neg_layer = Merge(mode="dot", dot_axes=-1, name="neg_layer")
    # neg_layer_ = neg_layer([word_embed_, item_neg_embed_])
    # neg_layer_ = dot([word_embed_, item_neg_embed_], axes=-1, normalize=False, name="neg_layer")
    neg_layer_ = Dot(axes=-1, normalize=False, name="neg_layer")([word_embed_, item_neg_embed_])
    # merge_layer = Merge(mode="concat", concat_axis=-1, name="merge_layer")
    # merge_layer_ = merge_layer([pos_layer_, neg_layer_])
    # merge_layer_ = concatenate([pos_layer_, neg_layer_], axis=-1, name="merge_layer")
    merge_layer_ = Concatenate(axis=-1, name="merge_layer")([pos_layer_, neg_layer_])

    # move the margin loss into loss function rather than merge layer
    # merge_layer = Merge(mode=lambda x: 0.5 - x[0] + x[1], output_shape=[1], name="merge_layer")
    # merge_layer_ = merge_layer([pos_layer_, neg_layer_])

    model = Model(input=[word_input, item_pos_input, item_neg_input], output=[merge_layer_, pos_layer_])

    def ranking_loss(y_true, y_pred):
        pos = y_pred[:,0]
        neg = y_pred[:,1]
        loss = K.maximum(0.5 + neg - pos, 0.0)
        return K.mean(loss) + 0 * y_true

    def dummy_loss(y_true, y_pred):
        # loss = K.max(y_pred) + 0 * y_true
        loss = y_pred + 0 * y_true
        return loss
    model.compile(optimizer=Adam(lr=0.01), loss = {'merge_layer' : ranking_loss, "pos_layer": dummy_loss}, loss_weights=[1, 0])

    print("finish model compiling")

    return model, word_embed, item_embed

if __name__ == '__main__':
    args = sys.argv
    if len(args) <= 10:
        args = [args[0], "model_ntm_2nd", "prod", "200", "5"]
    print(args)
    flag = args[1]
    n_processer = int(args[4])
    conf = Config(flag, args[2], int(args[3]))
    print(flag)

    # from tensorflow.python.client import device_lib
    # device_lib.list_local_devices()
    os.environ['MKL_NUM_THREADS'] = str(n_processer)
    os.environ['GOTO_NUM_THREADS'] = str(n_processer)
    os.environ['OMP_NUM_THREADS'] = str(n_processer)
    # os.environ['THEANO_FLAGS'] = 'device=gpu,blas.ldflags=-lblas -lgfortran'
    os.environ['THEANO_FLAGS'] = 'device=gpu'
    os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
    os.environ["CUDA_VISIBLE_DEVICES"]="0,1,2,3"
    config = tf.ConfigProto(log_device_placement=False, allow_soft_placement=True)
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 1
    session = tf.Session(config=config)
    K.set_session(session)

    # get data
    dp = DataProvider(conf)
    model, word_embed, item_embed = build_ntm_model(dp)

    print(model.summary())

    # target = np.array([9999] * len(word_data)) # useless since loss function make it times with 0
    if os.path.exists(conf.path_checkpoint):
        print("load previous checker")
        # model.load_weights(conf.path_checker)

    # model.fit(
    #     {"word_idx": word_data, "item_pos_idx": item_pos_data, "item_neg_idx": item_neg_data},
    #     {"merge_layer": target, "pos_layer": target},
    #     batch_size=conf.batch_size, nb_epoch=conf.n_epoch, validation_split=0.1,
    #     callbacks=[my_checker_point(item_embed, word_embed, model, conf),
    #                # my_value_checker([word_embed_, item_pos_embed_, item_neg_embed_, pos_layer_, neg_layer_, merge_layer_]),
    #                ModelCheckpoint(filepath=conf.path_checker, verbose=1, save_best_only=True)])

    dp.generate_init()
    model.fit_generator(generator=dp.generate_data(batch_size=conf.batch_size, is_validate=False), nb_worker=1, pickle_safe=False,
                        nb_epoch=conf.n_epoch, steps_per_epoch=int(np.ceil(conf.sample_per_epoch/conf.batch_size)),
                        validation_data = dp.generate_data(batch_size=conf.batch_size, is_validate=True), validation_steps=1,  #1913599
                        verbose=1, callbacks=[
                            my_checker_point(item_embed, word_embed, model, conf),
                            ModelCheckpoint(filepath=conf.path_checkpoint, verbose=1, save_best_only=True)
                        ])
