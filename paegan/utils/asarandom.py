import random
import uuid

class AsaRandom(object):

    @staticmethod
    def random():
        """
        pseudo random number generator
        """
        rand = random.random()
        flip = random.random()
        if flip > 0.5:
            rand *= -1
        return rand

    @staticmethod
    def filename(prefix=None, suffix=None):
        fn = []
        if prefix:
            fn.extend([prefix, '-'])

        fn.append(str(uuid.uuid4()))

        if suffix:
            fn.extend(['.', suffix.lstrip('.')])

        return ''.join(fn)
