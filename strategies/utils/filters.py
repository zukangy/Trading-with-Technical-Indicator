import numpy as np

from zipline.pipeline.filters import CustomFilter
from alphacompiler.data.SHARADAR_sectors import SHARADARStatic


class DomesticCommonStockFilter(CustomFilter):
    inputs = [SHARADARStatic().category]
    window_length = 1

    def compute(self, today, assets, out, cate):
        adr_codes = [13]
        out[:] = np.isin(cate, adr_codes)