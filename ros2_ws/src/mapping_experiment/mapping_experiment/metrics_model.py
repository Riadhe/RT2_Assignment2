"""
.. module:: metrics_model
   :platform: Unix
   :synopsis: Statistical model of one simulated 3D-mapping trial.

.. moduleauthor:: Riadh Bahri <s8335614@studenti.unige.it>

Generates per-trial metrics (latency, coverage, density, success) for a
(framework, scene) condition. Values are drawn from distributions
anchored to the real COGAR benchmark measurements; all distributional
assumptions are stated in data/anchors/anchors.yaml and in the paper.
ROS-free by design, so it can be tested in isolation.
"""

import math
import random

# Anchor values: real single-run measurements from the COGAR benchmark.
ANCHORS = {
    ("simple_room", "nvblox"):  {"latency_ms": 496,  "coverage_m3": 3.17,  "density_pts_m3": 88},
    ("simple_room", "rtabmap"): {"latency_ms": 6380, "coverage_m3": 9.49,  "density_pts_m3": 1073},
    ("simple_room", "octomap"): {"latency_ms": 459,  "coverage_m3": 2.93,  "density_pts_m3": 469},
    ("warehouse",  "nvblox"):   {"latency_ms": 386,  "coverage_m3": 2.65,  "density_pts_m3": 69},
    ("warehouse",  "rtabmap"):  {"latency_ms": 4628, "coverage_m3": 10.13, "density_pts_m3": 1280},
    ("warehouse",  "octomap"):  {"latency_ms": 1265, "coverage_m3": 5.98,  "density_pts_m3": 344},
}

# Stated dispersion assumptions (rationale in anchors.yaml).
LATENCY_SIGMA_LOG = {"nvblox": 0.12, "octomap": 0.12, "rtabmap": 0.20}
COVERAGE_CV = 0.05
DENSITY_CV = 0.08
SUCCESS_PROB = {
    ("simple_room", "nvblox"): 0.98, ("simple_room", "rtabmap"): 0.95,
    ("simple_room", "octomap"): 0.98,
    ("warehouse", "nvblox"): 0.95, ("warehouse", "rtabmap"): 0.85,
    ("warehouse", "octomap"): 0.92,
}

FRAMEWORKS = ("nvblox", "rtabmap", "octomap")
SCENES = ("simple_room", "warehouse")


def simulate_trial(scene, framework, trial_id, seed_base=12345):
    """Simulate one mapping trial and return its metrics.

    Args:
        scene (str): 'simple_room' or 'warehouse'.
        framework (str): 'nvblox', 'rtabmap' or 'octomap'.
        trial_id (int): trial index. Trial i of ALL frameworks shares
            the same scenario seed, which makes the design paired.
        seed_base (int): global experiment seed (reproducibility).

    Returns:
        dict: scene, framework, trial, latency_ms, coverage_m3,
        density_pts_m3, success.
    """
    anchor = ANCHORS[(scene, framework)]

    # Shared per-(scene, trial) scenario: same message timing / drop
    # pattern for every framework in this trial -> paired design.
    scenario_rng = random.Random(hash((seed_base, scene, trial_id)) & 0xFFFFFFFF)
    scenario_load = scenario_rng.gauss(0.0, 1.0)

    # Framework-specific residual noise.
    rng = random.Random(hash((seed_base, scene, framework, trial_id)) & 0xFFFFFFFF)

    # Latency: log-normal around the anchor median. 60% of the
    # log-deviation is the shared scenario load, 40% own jitter.
    sigma = LATENCY_SIGMA_LOG[framework]
    z = 0.6 * scenario_load + 0.4 * rng.gauss(0.0, 1.0)
    latency = anchor["latency_ms"] * math.exp(sigma * z)

    # Coverage and density: normal, truncated positive.
    cov = max(0.05, rng.gauss(anchor["coverage_m3"],
                              COVERAGE_CV * anchor["coverage_m3"]))
    den = max(1.0, rng.gauss(anchor["density_pts_m3"],
                             DENSITY_CV * anchor["density_pts_m3"]))

    # Success: Bernoulli; a failed trial yields a degraded partial map.
    success = 1 if rng.random() < SUCCESS_PROB[(scene, framework)] else 0
    if not success:
        cov *= rng.uniform(0.3, 0.6)
        den *= rng.uniform(0.5, 0.8)

    return {
        "scene": scene, "framework": framework, "trial": trial_id,
        "latency_ms": round(latency, 1),
        "coverage_m3": round(cov, 3),
        "density_pts_m3": round(den, 1),
        "success": success,
    }