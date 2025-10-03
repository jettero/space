# coding: utf-8


class Serial:
    @classmethod
    def to_save(cls):
        """enumerate (as a generator) all items in cls.Meta.save"""
        s = set()
        for c in cls.mro():
            try:
                for k in c.Meta.save:
                    if k not in s:
                        yield k
                        s.add(k)
            except AttributeError:
                pass

    def serial(self, skip_class=True, non_stop=False, full=False):
        """serialize all items from to_save().
        If any items in to_save() are '\x00', 0, False, or None,
        stop processing there and return results.
        params:
          skip_class=True : when false, populate 'm' and 'c' with module and class
          non_stop=False  : when True, don't stop on stop-processing items, simply skip those
          full=False      : set skip_class=False and non_stop=True
        """
        r = dict()
        if full:
            skip_class = False
            non_stop = True
        if not skip_class:
            r.update({"c": self.__class__.__name__, "m": self.__class__.__module__})
        for k in self.to_save():
            if k in ("\0", 0, False, None):
                if non_stop:
                    continue
                break
            r[k] = getattr(self, k, None)
        return r

    def as_dict(self, **kw):
        """return serial(full=True) merged with any given kwargs"""
        r = self.serial(full=True)
        r.update(kw)
        return r
