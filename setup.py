from setuptools import setup, find_packages

setup(name='himawari',
      version='0.0.1',
      description='Himawari8 satellite mosiac and video maker',
      url='https://github.com/nhoss2/himawari',
      author='Nafis Hossain',
      author_email='nafis@labs.im',
      license='',
      packages=find_packages(),
      install_requires=[
          'requests>=2.10.0', 'pytz>=2016.4'
      ],
      tests_require=['pytest']
)
