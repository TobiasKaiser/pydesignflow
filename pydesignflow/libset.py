class LibrarySet(list):
    """
    Is a list and not a set to prevent unexpected beahviour due to set being unordered (potentially randomly ordered).
    """
    def __getattr__(self, key):
        found_one = False
        for lib in self:
            try:
                yield getattr(lib, key)
            except AttributeError:
                pass
            else:
                found_one = True
        if not found_one:
            raise AttributeError()
