import torch
from torch.autograd import Function
from .._ext import roi_align


# TODO use save_for_backward instead
class RoIAlignFunction(Function):
    def __init__(self, aligned_height, aligned_width, spatial_scale):
        self.aligned_width = int(aligned_width)
        self.aligned_height = int(aligned_height)
        self.spatial_scale = float(spatial_scale)
        self.rois = None
        self.feature_size = None

    def forward(self, features, rois):
        batch_size, num_channels, data_height, data_width = features.size()
        num_rois = rois.size()[0]
        output = torch.zeros(num_rois, num_channels, self.aligned_height, self.aligned_width)

        # if not features.is_cuda:
        #     _features = features.permute(0, 2, 3, 1)
        #     roi_align.roi_align_forward(self.aligned_height, self.aligned_width, self.spatial_scale,
        #                                     _features, rois, output)
        #     # output = output.cuda()
        # else:
        assert features.is_cuda
        output = output.cuda()
        roi_align.roi_align_forward_cuda(self.aligned_height,
                                         self.aligned_width,
                                         self.spatial_scale, features,
                                         rois, output)
        self.output = output
        self.rois = rois
        self.feature_size = features.size()

        return output

    def backward(self, grad_output):
        assert(self.feature_size is not None and grad_output.is_cuda)

        batch_size, num_channels, data_height, data_width = self.feature_size

        grad_input = torch.zeros(batch_size, num_channels, data_height,
                                 data_width).cuda()
        roi_align.roi_align_backward_cuda(self.aligned_height,
                                          self.aligned_width,
                                          self.spatial_scale, grad_output,
                                          self.rois, grad_input)

        # print grad_input

        return grad_input, None