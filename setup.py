from setuptools import Extension, setup

setup(
  ext_modules=[
    Extension(
      name="nitrogfx.c_ext.tile",  # as it would be imported
      # may include packages/namespaces separated by `.`
      sources=["src/nitrogfx/c_ext/tilemodule.c"],  # all sources are compiled into a single binary file
    ),
  ]
)
