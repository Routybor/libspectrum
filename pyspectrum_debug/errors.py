class LoadError(Exception):
    def __int__(self, path: str):
        super().__init__(f'File {path} is not valid')


class MeasurementIncompatibleError(Exception):
    def __int__(self):
        super().__init__(f'Measurements were taken with different parameters')


class ConfigurationError(Exception):
    def __int__(self, what: str):
        super().__init__(what)


class DeviceClosedError(Exception):
    pass
