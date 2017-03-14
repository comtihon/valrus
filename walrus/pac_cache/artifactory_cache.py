from walrus.pac_cache import Cache
from walrus.packages.package import Package
from artifactory import ArtifactoryPath


class ArtifactoryCache(Cache):

    def exists(self, package: Package):
        pass

    def add_package(self, package: Package, rewrite: bool):
        pass

    def fetch_package(self, package: Package):
        pass

    def __init__(self, cache_url):
        super().__init__()
        self.path = cache_url

    def get_package(self, package: Package):
        pass