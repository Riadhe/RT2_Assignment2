from setuptools import setup

package_name = 'mapping_experiment'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Riadh Bahri',
    maintainer_email='s8335614@studenti.unige.it',
    description='Simulated 3D-mapping trials anchored to the COGAR benchmark.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'experiment_node = mapping_experiment.experiment_node:main',
        ],
    },
)
