# plain entity 2 vec model
import os
from keras.models import Model
from keras.layers import Input
from keras.layers.core import *
from keras.layers.embeddings import *

from entity.beta.data import DataProvider
from keras.callbacks import ModelCheckpoint
import numpy as np
from entity.config import Config
from keras.optimizers import *
import numpy as np
import theano
import sys
from keras.layers.merge import dot, concatenate, Dot, Concatenate

from entity.model.callbacks import my_checker_point


def build_attr_model(dp):
    n_terms = len(dp.idx2word)
    n_prods = len(dp.idx2prod)
    n_tags = len(dp.idx2tag)

    # initialize parameters (embeddings and W)
    word_embed_data = np.array(dp.word_embed)
    prod_embed_data = np.random.rand(n_prods, conf.dim_item)
    tag_embed_data = np.random.rand(n_tags, conf.dim_item)
    word_transfer_W = np.random.rand(conf.dim_word, conf.dim_item)
    word_transfer_b = np.random.rand(conf.dim_item)
    print("finish data processing")

    # define model
    wd_word_idx_input = Input(shape=(1,), dtype ="int32", name ="wd_word_idx")
    wd_pos_doc_idx_input = Input(shape=(1,), dtype ="int32", name ="wd_pos_doc_idx")
    wd_neg_doc_idx_input = Input(shape=(1,), dtype ="int32", name ="wd_neg_doc_idx")

    wt_word_idx_input = Input(shape=(1,), dtype ="int32", name ="wt_word_idx")
    wt_pos_tag_idx_input = Input(shape=(1,), dtype ="int32", name ="wt_pos_tag_idx")
    wt_neg_tag_idx_input = Input(shape=(1,), dtype ="int32", name ="wt_neg_tag_idx")

    dt_pos_doc_idx_input = Input(shape=(1,), dtype ="int32", name ="dt_pos_doc_idx")
    dt_pos_tag_idx_input = Input(shape=(1,), dtype ="int32", name ="dt_pos_tag_idx")
    dt_neg_doc_idx_input = Input(shape=(1,), dtype ="int32", name ="dt_neg_doc_idx")
    dt_neg_tag_idx_input = Input(shape=(1,), dtype ="int32", name ="dt_neg_tag_idx")

    word_embed = Embedding(output_dim=conf.dim_word, input_dim=n_terms, input_length=1, name="word_embed",
                           weights=[word_embed_data], trainable=False)
    prod_embed = Embedding(output_dim=conf.dim_item, input_dim=n_prods, input_length=1, name="prod_embed",
                           weights=[prod_embed_data], trainable=True)
    tag_embed = Embedding(output_dim=conf.dim_item, input_dim=n_tags, input_length=1, name="tag_embed",
                           weights=[tag_embed_data], trainable=True)
    word_transfer = Dense(activation="sigmoid", output_dim=conf.dim_item, input_dim=conf.dim_word, trainable=True,
                        weights=[word_transfer_W, word_transfer_b], name="word_transfer")
    item_activate = Activation(activation="softmax", name="item_activate")

    # -----   Word-Doc section -----
    wd_word_idx = word_embed(wd_word_idx_input)
    wd_pos_doc_idx = prod_embed(wd_pos_doc_idx_input)
    wd_neg_doc_idx = prod_embed(wd_neg_doc_idx_input)

    wd_word_idx = Flatten()(wd_word_idx)
    wd_word_idx = word_transfer(wd_word_idx)
    wd_pos_doc_idx = Flatten()(wd_pos_doc_idx)
    wd_neg_doc_idx = Flatten()(wd_neg_doc_idx)
    wd_pos_doc_idx = item_activate(wd_pos_doc_idx)
    wd_neg_doc_idx = item_activate(wd_neg_doc_idx)

    # wd_pos_merge = Merge(mode="dot", dot_axes=-1, name="wd_pos_merge")([wd_word_idx, wd_pos_doc_idx])
    wd_pos_merge = Dot(axes=-1, normalize=False, name="wd_pos_merge")([wd_word_idx, wd_pos_doc_idx])
    # wd_neg_merge = Merge(mode="dot", dot_axes=-1, name="wd_neg_merge")([wd_word_idx, wd_neg_doc_idx])
    wd_neg_merge = Dot(axes=-1, normalize=False, name="wd_neg_merge")([wd_word_idx, wd_neg_doc_idx])

    # -----  Word-Tag section  -----
    wt_word_idx = word_embed(wt_word_idx_input)
    wt_pos_tag_idx = tag_embed(wt_pos_tag_idx_input)
    wt_neg_tag_idx = tag_embed(wt_neg_tag_idx_input)

    wt_word_idx = Flatten()(wt_word_idx)
    wt_word_idx = word_transfer(wt_word_idx)
    wt_pos_tag_idx = Flatten()(wt_pos_tag_idx)
    wt_neg_tag_idx = Flatten()(wt_neg_tag_idx)
    wt_pos_tag_idx = item_activate(wt_pos_tag_idx)
    wt_neg_tag_idx = item_activate(wt_neg_tag_idx)

    # wt_pos_merge = Merge(mode="dot", dot_axes=-1, name="wt_pos_merge")([wt_word_idx, wt_pos_tag_idx])
    wt_pos_merge = Dot(axes=-1, normalize=False, name="wt_pos_merge")([wt_word_idx, wt_pos_tag_idx])
    # wt_neg_merge = Merge(mode="dot", dot_axes=-1, name="wt_neg_merge")([wt_word_idx, wt_neg_tag_idx])
    wt_neg_merge = Dot(axes=-1, normalize=False, name="wt_neg_merge")([wt_word_idx, wt_neg_tag_idx])

    # -----  Doc-Tag section  -----
    dt_pos_doc_idx = prod_embed(dt_pos_doc_idx_input)
    dt_neg_doc_idx = prod_embed(dt_neg_doc_idx_input)
    dt_pos_tag_idx = tag_embed(dt_pos_tag_idx_input)
    dt_neg_tag_idx = tag_embed(dt_neg_tag_idx_input)

    dt_pos_doc_idx = Flatten()(dt_pos_doc_idx)
    dt_neg_doc_idx = Flatten()(dt_neg_doc_idx)
    dt_pos_tag_idx = Flatten()(dt_pos_tag_idx)
    dt_neg_tag_idx = Flatten()(dt_neg_tag_idx)
    dt_pos_doc_idx = item_activate(dt_pos_doc_idx)
    dt_neg_doc_idx = item_activate(dt_neg_doc_idx)
    # dt_pos_tag_idx = tag_embed(dt_pos_tag_idx)
    # dt_neg_tag_idx = tag_embed(dt_neg_tag_idx)

    # dt_pos_merge = Merge(mode="dot", dot_axes=-1, name="dt_pos_merge")([dt_pos_doc_idx, dt_pos_tag_idx])
    dt_pos_merge = Dot(axes=-1, normalize=False, name="dt_pos_merge")([dt_pos_doc_idx, dt_pos_tag_idx])
    # dt_neg_merge1 = Merge(mode="dot", dot_axes=-1, name="dt_neg_merge1")([dt_pos_doc_idx, dt_neg_tag_idx])
    dt_neg_merge1 = Dot(axes=-1, normalize=False, name="dt_neg_merge1")([dt_pos_doc_idx, dt_neg_tag_idx])
    # dt_neg_merge2 = Merge(mode="dot", dot_axes=-1, name="dt_neg_merge2")([dt_neg_doc_idx, dt_pos_tag_idx])
    dt_neg_merge2 = Dot(axes=-1, normalize=False, name="dt_neg_merge2")([dt_neg_doc_idx, dt_pos_tag_idx])

    # ----- Combine section -----
    # final_merge = Merge(mode="concat", concat_axis=-1, name="final_merge")([wd_pos_merge, wd_neg_merge,
    #                                                                          wt_pos_merge, wt_neg_merge,
    #                                                                          dt_pos_merge, dt_neg_merge1, dt_neg_merge2
    #                                                                          ])
    final_merge = Concatenate(axis=-1, name="final_merge")([wd_pos_merge, wd_neg_merge,
                                                                             wt_pos_merge, wt_neg_merge,
                                                                             dt_pos_merge, dt_neg_merge1, dt_neg_merge2
                                                                             ])

    model = Model(input=[wd_word_idx_input, wd_pos_doc_idx_input, wd_neg_doc_idx_input,
                         wt_word_idx_input, wt_pos_tag_idx_input, wt_neg_tag_idx_input,
                         dt_pos_doc_idx_input, dt_pos_tag_idx_input, dt_neg_doc_idx_input, dt_neg_tag_idx_input],
                  output=final_merge)

    def ranking_loss(y_true, y_pred):
        wd_pos_score = y_pred[:,0]
        wd_neg_score = y_pred[:, 1]
        wt_pos_score = y_pred[:, 2]
        wt_neg_score = y_pred[:, 3]
        dt_pos_score = y_pred[:, 4]
        dt_neg_score1 = y_pred[:, 5]
        dt_neg_score2 = y_pred[:, 6]
        loss = K.maximum(0.5 + wd_neg_score - wd_pos_score, 0.0) + K.maximum(0.5 + wt_neg_score - wt_pos_score, 0.0) \
               + K.maximum(0.5 + dt_neg_score1 + dt_neg_score2 - dt_pos_score, 0.0)
        return K.mean(loss) + 0 * y_true


    model.compile(optimizer=Adam(lr=lr), loss = {'final_merge' : ranking_loss})

    print("finish model compiling")
    print(model.summary())

    return model, word_embed, prod_embed, tag_embed

if __name__ == '__main__':

    args = sys.argv
    if len(args) <= 1:
        args = [args[0], "attribute-argumented_model.freq=100", "full", "200", "1", "0.01"]

    flag = args[1]
    n_processer = int(args[4])
    lr = float(args[5])
    print(args)
    os.environ['MKL_NUM_THREADS'] = str(n_processer)
    os.environ['GOTO_NUM_THREADS'] = str(n_processer)
    os.environ['OMP_NUM_THREADS'] = str(n_processer)
    os.environ['THEANO_FLAGS'] = 'device=cpu,blas.ldflags=-lblas -lgfortran'

    import os

    os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
    os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"
    config = tf.ConfigProto(log_device_placement=False, allow_soft_placement=True)
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 1

    conf = Config(flag, args[2], int(args[3]))
    print(flag)
    print(theano.config.openmp)

    # get data
    dp = DataProvider(conf)
    model, word_embed, prod_embed, tag_embed = build_attr_model(dp)

    if os.path.exists(conf.path_checkpoint):
        print("load previous checker")
        model.load_weights(conf.path_checkpoint)


    dp.generate_init()
    model.fit_generator(generator=dp.generate_data(batch_size=conf.batch_size), nb_worker=n_processer,
                        nb_epoch=conf.n_epoch, samples_per_epoch=int(np.ceil(conf.sample_per_epoch / conf.batch_size)),
                        validation_data=dp.generate_data(batch_size=conf.batch_size), validation_steps=1,
                        callbacks=[
                            my_checker_point(prod_embed, word_embed, model, conf, tag_embed),
                            ModelCheckpoint(filepath=conf.path_checkpoint, verbose=1, save_best_only=True)
                        ])