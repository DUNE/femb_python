"""
setup.py for femb_python

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='femb_python',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.0.2',

    description='DUNE/SBND Cold Electronics Testing Package',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/DUNE/femb_python',

    # Author details
    author='The DUNE/SBND Cold Electronics Project',
    author_email='jhugon@fnal.fake',

    # Choose your license
    license='',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='testing particle physics',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'numpy>=1.7.1',
        'matplotlib>=1.2.1',
	'future>=0.15.2',
	'configparser>=3.5.0',
        'sumatra>=0.5.1',
        'gitpython>=2.1.3',
        'psycopg2>=2.7.1'
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
    #    'dev': ['check-manifest'],
    #    'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    #package_data={
    #    'femb_python': [
    #                        'configuration/adctest.ini',
    #                    ],
    #},
    include_package_data=True,

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'femb_gui=femb_python.configuration_window:main',
            'femb_show_trace_fft=femb_python.trace_fft_window:main',
            'femb_dump_data_root=femb_python.write_root_tree:main',
            'femb_show_trace_root=femb_python.helper_scripts.show_trace_root:main',

            'femb_init_board=femb_python.helper_scripts.init_board:main',
            'femb_read_reg=femb_python.helper_scripts.read_reg:main',
            'femb_write_reg=femb_python.helper_scripts.write_reg:main',
            'femb_dump_data=femb_python.helper_scripts.dump_data:main',
            'femb_select_channel=femb_python.helper_scripts.select_channel:main',
            'femb_measureRMS=femb_python.helper_scripts.measureRms:main',
            'femb_sync_adc=femb_python.helper_scripts.sync_adc:main',
            'femb_config_adc=femb_python.helper_scripts.config_adc:main',
            'femb_config_fe=femb_python.helper_scripts.config_fe:main',
            'femb_lock=femb_python.helper_scripts.locking:lock',

            'femb_power_supply=femb_python.helper_scripts.test_instruments:powersupply',
            'femb_function_generator=femb_python.helper_scripts.test_instruments:funcgen',

            'femb_adc_static_tests=femb_python.test_measurements.adc_test_stand.static_tests:main',
            'femb_adc_dynamic_tests=femb_python.test_measurements.adc_test_stand.dynamic_tests:main',
            'femb_adc_collect_data=femb_python.test_measurements.adc_test_stand.collect_data:main',
            'femb_adc_calibrate_ramp=femb_python.test_measurements.adc_test_stand.calibrate_ramp:main',
            'femb_adc_baseline_rms=femb_python.test_measurements.adc_test_stand.baseline_rms:main',
            'femb_adc_dc_tests=femb_python.test_measurements.adc_test_stand.dc_tests:main',
            'femb_adc_run=femb_python.test_measurements.adc_test_stand.run:main',
            'femb_adc_summary_plots=femb_python.test_measurements.adc_test_stand.summary_plots:main',
            'femb_adc_ranking=femb_python.test_measurements.adc_test_stand.ranking:main',
            'femb_adc_gui=femb_python.test_measurements.adc_test_stand.gui:main',

            'femb_example_measure_simple=femb_python.test_measurements.example_femb_test.doFembTest_simpleMeasurement:main',
            'femb_example_measure_gain=femb_python.test_measurements.example_femb_test.doFembTest_gainMeasurement:main',
            'femb_example_measure_noise=femb_python.test_measurements.example_femb_test.doFembTest_noiseMeasurement:main',

            'femb_wib_setup_clock=femb_python.test_measurements.wibTestStand.setup_wib_clock:main',
            'femb_wib_setup_protodune=femb_python.test_measurements.wibTestStand.setup_wib_protodune:main',
            'femb_wib_gui=femb_python.test_measurements.wibTestStand.wib_configuration_window:main',
            'femb_wib_trace_fft=femb_python.test_measurements.wibTestStand.trace_fft_window_wib:main',
            'femb_wib_allchan_trace_fft=femb_python.test_measurements.wibTestStand.wib_trace_fft_allchan_window:main',
            'femb_wib_measure_gain=femb_python.test_measurements.wibTestStand.doFembTest_gainMeasurement:main',
            'femb_wib_measure_noise=femb_python.test_measurements.wibTestStand.doFembTest_noiseMeasurement:main',
            'femb_wib_measure_simple=femb_python.test_measurements.wibTestStand.doFembTest_simpleMeasurement:main',
            'femb_wib_test_simpleCheck=femb_python.test_measurements.wibTestStand.doWibTest_simpleCheck:main',

            'femb_feasic_testgui=femb_python.test_measurements.feAsicTest.gui_feAsicTest:main',
            'femb_feasic_simple=femb_python.test_measurements.feAsicTest.doFembTest_simpleMeasurement:main',
            'femb_feasic_gain=femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement:main',
            'femb_feasic_gain_fpgadac=femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement_fpgaDac:main',
            'femb_feasic_gain_externaldac=femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement_externalDac:main',
            'femb_control_power=femb_python.test_measurements.feAsicTest.doFemb_controlPower:main',

        ],
        #'gui_scripts': [
        #    'femb_test=femb_python.gui:main',
        #],
    },
)
