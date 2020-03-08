import tensorflow as tf
from tensorflow.keras import layers

from . import ops


class PWCNet(tf.keras.Model):
    def __init__(self,
                 max_displacement=4,
                 name='pwcnet'):
        super().__init__(name=name)
        self.max_displacement = max_displacement

        self.extractor = ops.FeaturePyramidExtractor(name='extractor')
        self.warp = ops.warp
        self.cost_volume = ops.CostVolume(max_displacement, name='cost_volume')

        self.estimator2 = ops.OpticalFlowEstimator(upsample=False,
                                                   name='estimator2')
        self.estimator3 = ops.OpticalFlowEstimator(name='estimator3')
        self.estimator4 = ops.OpticalFlowEstimator(name='estimator4')
        self.estimator5 = ops.OpticalFlowEstimator(name='estimator5')
        self.estimator6 = ops.OpticalFlowEstimator(name='estimator6')

        self.context = ops.ContextNetwork(name='context')
        self.resize = layers.UpSampling2D((4, 4), interpolation='bilinear',
                                          name='resize')

    def call(self, x):
        x1, x2 = x
        c16, c15, c14, c13, c12, c11 = self.extractor(x1)
        c26, c25, c24, c23, c22, c21 = self.extractor(x2)

        cv6 = self.cost_volume((c16, c26))
        flow6, upflow6, upfeat6 = self.estimator6((cv6, c16))

        warp5 = self.warp(c25, upflow6*0.625)
        cv5 = self.cost_volume((c15, warp5))
        flow5, upflow5, upfeat5 = self.estimator5((cv5, c15, upflow6, upfeat6))

        warp4 = self.warp(c24, upflow5*1.25)
        cv4 = self.cost_volume((c14, warp4))
        flow4, upflow4, upfeat4 = self.estimator4((cv4, c14, upflow5, upfeat5))

        warp3 = self.warp(c23, upflow4*2.5)
        cv3 = self.cost_volume((c13, warp3))
        flow3, upflow3, upfeat3 = self.estimator3((cv3, c13, upflow4, upfeat4))

        warp2 = self.warp(c22, upflow3*5.0)
        cv2 = self.cost_volume((c12, warp2))
        flow2, x = self.estimator2((cv2, c12, upflow3, upfeat3))

        flow2 = self.context((flow2, x))
        flow = self.resize(flow2)*20.0
        return flow, [flow2, flow3, flow4, flow5, flow6]