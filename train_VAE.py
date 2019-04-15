#!/usr/bin/python3

import os;
import tensorflow as tf;
import tensorflow_probability as tfp;
from VAE import VAE;

batch_size = 100;

def parse_function(serialized_example):
    feature = tf.io.parse_single_example(
        serialized_example,
        features = {
            'data':tf.io.FixedLenFeature((),dtype = tf.string,default_value = ''),
            'label':tf.io.FixedLenFeature((),dtype = tf.int64,default_value = 0)
        }
    );
    data = tf.io.decode_raw(feature['data'],out_type = tf.uint8);
    data = tf.reshape(data,[28,28,1]);
    data = tf.cast(data,dtype = tf.float32);
    label = tf.cast(feature['label'],dtype = tf.int32);
    return data,label;

def main():
    
    vae = VAE();
    optimizer = tf.keras.optimizers.Adam(1e-3);
    #load dataset
    trainset = tf.data.TFRecordDataset(os.path.join('dataset','trainset.tfrecord')).map(parse_function).shuffle(batch_size).batch(batch_size);
    testset = tf.data.TFRecordDataset(os.path.join('dataset','testset.tfrecord')).map(parse_function).batch(batch_size);
    #restore from existing checkpoint
    if False == os.path.exists('vae_checkpoints'): os.mkdir('vae_checkpoints');
    checkpoint = tf.train.Checkpoint(model = vae, optimizer = optimizer, optimizer_step = optimizer.iterations);
    checkpoint.restore(tf.train.latest_checkpoint('vae_checkpoints'));
    #create log
    log = tf.summary.create_file_writer('vae_checkpoints');
    #train model
    print('training');
    avg_loss = tf.keras.metrics.Mean(name = 'loss', dtype = tf.float32);
    while True:
        for (images, labels) in trainset:
            with tf.GradientTape() as tape:
                loss = vae(images);
                avg_loss.update_state(loss);
            #write log
            if tf.equal(optimizer.iterations % 100, 0):
                with log.as_default():
                    tf.summary.scalar('loss',avg_loss.result(), step = optimizer.iterations);
                    for i in range(10):
                        tf.summary.image(str(i),vae.sample(), step = optimizer.iterations);
                print('Step #%d Loss: %.6f' % (optimizer.iterations, avg_loss.result()));
                avg_loss.reset_states();
            grads = tape.gradient(loss, vae.trainable_variables);
            optimizer.apply_gradients(zip(grads, vae.trainable_variables));
        #save check point
        checkpoint.save(os.path.join('vae_checkpoints','ckpt'));

if __name__ == "__main__":
    
    assert tf.executing_eagerly();
    main();

