
import os
import glob
import json
import argparse
from utils.utils import calc_mean_score, save_json
from handlers.model_builder import Nima
from handlers.data_generator import TestDataGenerator
from PIL import Image


def image_file_to_json(img_path):
    img_dir = os.path.dirname(img_path)
    #img_id = os.path.basename(img_path).split('.')[0]
    bn = os.path.basename(img_path)
    img_id = bn[:bn.rfind('.')]
    img_format = bn[bn.rfind('.')+1:]

    return img_dir, [{'image_id': img_id, 'image_format': img_format}]


def image_dir_to_json(img_dir, img_type='jpg'):
    #img_paths = glob.glob(os.path.join(img_dir, '*.'+img_type))
    img_paths = glob.glob(os.path.join(img_dir, '*'))

    samples = []
    for img_path in img_paths:

        try:
            bn = os.path.basename(img_path)
            if bn.rfind('.')<0:
                print("WARNING: skipping file %s since it has no extension" % (bn))
                continue

            im = Image.open(img_path)  # will throw exception if it does not contain an image

            #img_id = os.path.basename(img_path).split('.')[0]
            img_id = bn[:bn.rfind('.')]
            img_format = bn[bn.rfind('.')+1:]
            samples.append({'image_id': img_id, 'image_format': img_format})
        except Exception as e:
            print("WARNING: skipping file %s, it cannot be decoded as image: %s" % (img_path, e))

    return samples


def predict(model, data_generator):
    return model.predict_generator(data_generator, workers=8, use_multiprocessing=True, verbose=1)


def main(base_model_name, weights_file, image_source, predictions_file, img_format='jpg'):
    # load samples
    if os.path.isfile(image_source):
        image_dir, samples = image_file_to_json(image_source)
    else:
        image_dir = image_source
        samples = image_dir_to_json(image_dir, img_type='jpg')

    # build model and load weights
    nima = Nima(base_model_name, weights=None)
    nima.build()
    nima.nima_model.load_weights(weights_file)

    # initialize data generator
    data_generator = TestDataGenerator(samples, image_dir, 64, 10, nima.preprocessing_function(),
                                       img_format=img_format)

    # get predictions
    predictions = predict(nima.nima_model, data_generator)

    # calc mean scores and add to samples
    for i, sample in enumerate(samples):
        sample['mean_score_prediction'] = calc_mean_score(predictions[i])
        sample['score_distribution'] = predictions[i].tolist()

    print(json.dumps(samples, indent=2))

    if predictions_file is not None:
        save_json(samples, predictions_file)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base-model-name', help='CNN base model name', required=True)
    parser.add_argument('-w', '--weights-file', help='path of weights file', required=True)
    parser.add_argument('-is', '--image-source', help='image directory or file', required=True)
    parser.add_argument('-pf', '--predictions-file', help='file with predictions', required=False, default=None)

    args = parser.parse_args()

    main(**args.__dict__)
