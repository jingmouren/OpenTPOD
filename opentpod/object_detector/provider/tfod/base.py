"""Tensorflow Object Detection API provider
"""
import subprocess
import re
import multiprocessing

from logzero import logger
from mako import template

from opentpod.object_detector.provider import utils


class TFODDetector():
    """Tensorflow Object Detection API
    See: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/running_locally.md
    """

    def __init__(self, config):
        """Expected directory layout
            +data
                -label_map file
                -train TFRecord file
                -eval TFRecord file
            +models
                + model
                    -pipeline config file
                    +train
                    +eval
        Arguments:
            config: contains input_dir, output_dir, and training parameters
            db_detector: object_detection.models.Detector
            db_detector: object_detection.models.TrainConfig
        """
        super().__init__()
        self._config = config
        self._input_dir = self._config['input_dir']
        self._output_dir = self._config['output_dir']
        # find appropriate model to finetune from
        self.cache_pretrained_model()

    @property
    def required_parameters(self):
        return []

    @property
    def optional_parameters(self):
        return {}

    @property
    def pretrained_model_cache_entry(self):
        return self.__class__.__name__ + '-pretrained-model'

    @property
    def pretrained_model_url(self):
        raise NotImplementedError()

    @property
    def pipeline_config_template(self):
        raise NotImplementedError()

    def cache_pretrained_model(self):
        """Download and cache pretrained model if not existed."""
        if utils.get_cache_entry(self.pretrained_model_cache_entry) is None:
            logger.info('downloading and caching pretrained model from tensorflow website')
            logger.info('url: {}'.format(self.pretrained_model_url))
            utils.download_and_extract_url_tarball_to_cache_dir(
                self.pretrained_model_url, self.pretrained_model_cache_entry)

    def get_pretrained_model_checkpoint(self):
        cache_entry_dir = utils.get_cache_entry(self.pretrained_model_cache_entry)
        potential_pretained_model_files = list(cache_entry_dir.glob('**/model.ckpt*'))
        if len(potential_pretained_model_files) == 0:
            raise ValueError('Failed to find pretrained model in {}'.format(cache_entry_dir))
        fine_tune_model_dir = potential_pretained_model_files[0].parent
        return str(fine_tune_model_dir.resolve() / 'model.ckpt')

    def prepare_config(self):
        # fill in on-disk file structure to config
        self._config['pipeline_config_path'] = str(self._input_dir.resolve() / 'pipeline.config')
        self._config['train_input_path'] = str(self._input_dir.resolve() / 'train.tfrecord')
        self._config['eval_input_path'] = str(self._input_dir.resolve() / 'eval.tfrecord')
        self._config['label_map_path'] = str(self._input_dir.resolve() / 'label_map.pbtxt')

        # num_classes are the number of classes to learn
        with open(self._config['label_map_path'], 'r') as f:
            content = f.read()
            labels = re.findall(r"\tname: '(\w+)'\n", content)
            self._config['num_classes'] = len(labels)

        # fine_tune_checkpoint should point to the path of the checkpoint from
        # which transfer learning is done
        if ('fine_tune_checkpoint' not in self._config) or (
                self._config['fine_tune_checkpoint'] is None):
            self._config['fine_tune_checkpoint'] = self.get_pretrained_model_checkpoint()

        # make sure all required parameter is given
        for parameter in self.required_parameters:
            if parameter not in self._config:
                raise ValueError('Parameter ({}) is required, but not given'.format(paramter))

        # use default values for optional parameters if not given
        for parameter, value in self.optional_parameters.items():
            if parameter not in self._config:
                self._config[parameter] = value

    def prepare_config_pipeline_file(self):
        pipeline_config = template.Template(
            self.pipeline_config_template).render(**self._config)
        #     num_classes=self._config['num_classes'],
        #     fine_tune_checkpoint=self._config['fine_tune_checkpoint'],
        #     batch_size=self._config['batch_size'],
        #     num_steps=self._config['num_steps'],
        #     train_input_path=self._config['train_input_path'],
        #     eval_input_path=self._config['eval_input_path'],
        #     label_map_path=self._config['label_map_path']
        # )
        with open(self._config['pipeline_config_path'], 'w') as f:
            f.write(pipeline_config)

    def prepare(self):
        """Prepare files needed for training."""
        self.prepare_config()
        self.prepare_config_pipeline_file()

    def train(self):
        # need to run tf train with subprocess as tf has problem with python's
        # multiprocess module
        # see: https://github.com/tensorflow/tensorflow/issues/5448
        train_cmd = 'python -m opentpod.object_detector.provider.tfod.tfod_train_wrapper --pipeline_config_path={0} --model_dir={1} --alsologtostderr'.format(
            self._config['pipeline_config_path'],
            self._output_dir
        )
        logger.info('launching training process with following command: \n\n{}'.format(train_cmd))
        process = subprocess.Popen(
            train_cmd.split())
        return process.pid

    def run(self):
        pass
