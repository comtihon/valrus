import json
import test
import unittest
from os import listdir
from os.path import join

import os
from mock import patch

from coon.__main__ import create
from coon.pac_cache.local_cache import LocalCache
from coon.packages.package import Package
from coon.packages.package_builder import Builder
from coon.utils.file_utils import remove_dir, copy_file
from test.abs_test_class import TestClass


def mock_fetch_package(dep: Package):
    test_dir = test.get_test_dir('local_cache_tests')
    tmp_path = join(os.getcwd(), test_dir, 'tmp')
    dep.update_from_cache(join(tmp_path, dep.name))


class LocalCacheTests(TestClass):
    def __init__(self, method_name):
        super().__init__('local_cache_tests', method_name)

    def setUp(self):
        super().setUp()
        create(self.test_dir, {'<name>': 'test_app'})

    # Tests if package exists in local cache
    @patch('coon.global_properties.ensure_conf_file')
    def test_package_exists(self, mock_conf):
        mock_conf.return_value = self.conf_file
        pack_path = join(self.test_dir, 'test_app')
        set_url(pack_path, 'https://github.com/comtihon/test_app')
        pack = Package.from_path(pack_path)
        builder = Builder.init_from_path(pack_path)
        self.assertEqual(False, builder.system_config.cache.exists_local(pack))
        self.assertEqual(True, builder.build())
        builder.system_config.cache.add_package_local(pack)
        self.assertEqual(True, builder.system_config.cache.exists_local(pack))

    # Test if test_app.cp can be added to local cache
    @patch('coon.global_properties.ensure_conf_file')
    def test_add_from_package(self, mock_conf):
        mock_conf.return_value = self.conf_file
        pack_path = join(self.test_dir, 'test_app')
        set_url(pack_path, 'https://github.com/comtihon/test_app')
        builder = Builder.init_from_path(pack_path)
        self.assertEqual(True, builder.build())
        builder.package()
        new_package_path = join(self.test_dir, 'test_app.cp')
        # remove source project, test should work only with coon package
        copy_file(join(pack_path, 'test_app.cp'), new_package_path)
        remove_dir(pack_path)
        package = Package.from_package(new_package_path)
        self.assertEqual(False, builder.system_config.cache.exists_local(package))
        # local cache is used here to determine tmp dir
        local_cache = builder.system_config.cache.local_cache
        builder.system_config.cache.add_fetched(local_cache, package)
        self.assertEqual(True, builder.system_config.cache.exists_local(package))

    # Test if test_app can be added to local cache
    @patch('coon.global_properties.ensure_conf_file')
    def test_add_from_path(self, mock_conf):
        mock_conf.return_value = self.conf_file
        pack_path = join(self.test_dir, 'test_app')
        set_url(pack_path, 'https://github.com/comtihon/test_app')
        builder = Builder.init_from_path(pack_path)
        self.assertEqual(True, builder.build())
        self.assertEqual(False, builder.system_config.cache.exists_local(builder.project))
        builder.system_config.cache.add_package_local(builder.project)
        self.assertEqual(True, builder.system_config.cache.exists_local(builder.project))

    # Test if test_app can be fetched, compiled and added to local cache
    def test_compile_and_add(self):
        self.assertEqual(True, True)

    # Test if test_app has several deps, all will be fetched, compiled and added to local cache
    @patch.object(LocalCache, 'fetch_package', side_effect=mock_fetch_package)
    @patch('coon.global_properties.ensure_conf_file')
    def test_add_with_deps(self, mock_conf, _):
        mock_conf.return_value = self.conf_file
        # Create test_app with deps: A and B
        pack_path = join(self.test_dir, 'test_app')
        set_deps(pack_path,
                 [
                     {'name': 'a_with_dep_a2',
                      'url': 'https://github.com/comtihon/a_with_dep_a2',
                      'vsn': '1.0.0'},
                     {'name': 'b_with_no_deps',
                      'url': 'https://github.com/comtihon/b_with_no_deps',
                      'vsn': '1.0.0'}
                 ])
        # Create dep A with dep A2 (in tmp, as if we download them from git)
        create(self.tmp_dir, {'<name>': 'a_with_dep_a2'})
        dep_a1_path = join(self.tmp_dir, 'a_with_dep_a2')
        set_url(dep_a1_path, 'https://github.com/comtihon/a_with_dep_a2')
        set_deps(dep_a1_path, [{'name': 'a2_with_no_deps',
                                'url': 'https://github.com/comtihon/a2_with_no_deps',
                                'vsn': '1.0.0'}])
        # Create dep B (in tmp, as if we download them from git)
        create(self.tmp_dir, {'<name>': 'b_with_no_deps'})
        dep_b_path = join(self.tmp_dir, 'b_with_no_deps')
        set_url(dep_b_path, 'https://github.com/comtihon/b_with_no_deps')
        # Create dep A2 (in tmp, as if we download them from git)
        create(self.tmp_dir, {'<name>': 'a2_with_no_deps'})
        dep_a2_path = join(self.tmp_dir, 'a2_with_no_deps')
        set_url(dep_a2_path, 'https://github.com/comtihon/a2_with_no_deps')
        # Compile test_project
        builder = Builder.init_from_path(pack_path)
        self.assertEqual(False, builder.system_config.cache.exists_local(Package.from_path(dep_a1_path)))
        self.assertEqual(False, builder.system_config.cache.exists_local(Package.from_path(dep_b_path)))
        self.assertEqual(False, builder.system_config.cache.exists_local(Package.from_path(dep_a2_path)))
        builder.populate()
        self.assertEqual(True, builder.build())
        self.assertEqual(True, builder.system_config.cache.exists_local(Package.from_path(dep_a1_path)))
        self.assertEqual(True, builder.system_config.cache.exists_local(Package.from_path(dep_b_path)))
        self.assertEqual(True, builder.system_config.cache.exists_local(Package.from_path(dep_a2_path)))


def set_url(path: str, url: str):
    fullpath = join(path, 'coonfig.json')
    with open(fullpath, 'r') as file:
        conf = json.load(file)
    conf['url'] = url
    with open(fullpath, 'w') as file:
        json.dump(conf, file)


def set_deps(path: str, deps: list):
    fullpath = join(path, 'coonfig.json')
    with open(fullpath, 'r') as file:
        conf = json.load(file)
    conf['deps'] = deps
    with open(fullpath, 'w') as file:
        json.dump(conf, file)


if __name__ == '__main__':
    unittest.main()