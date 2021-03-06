import gym
import pytest

from smarts.core.utils.episodes import episodes
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.core.agent import AgentSpec, AgentPolicy

AGENT_ID = "Agent-007"
SOCIAL_AGENT_ID = "Alec Trevelyan"

MAX_EPISODES = 3


@pytest.fixture
def agent_spec():
    return AgentSpec(
        interface=AgentInterface.from_type(AgentType.Laner, max_episode_steps=100),
        policy_builder=lambda: AgentPolicy.from_function(lambda _: "keep_lane"),
    )


@pytest.fixture
def env(agent_spec):
    env = gym.make(
        "smarts.env:hiway-v0",
        scenarios=["scenarios/zoo_intersection"],
        agent_specs={AGENT_ID: agent_spec},
        headless=True,
        visdom=False,
        timestep_sec=0.01,
    )

    yield env
    env.close()


def test_social_agents(env, agent_spec):
    for episode in episodes(n=MAX_EPISODES):
        agent = agent_spec.build_agent()
        observations = env.reset()
        episode.record_scenario(env.scenario_log)

        dones = {"__all__": False}
        while not dones["__all__"]:
            obs = observations[AGENT_ID]
            observations, rewards, dones, infos = env.step({AGENT_ID: agent.act(obs)})
            episode.record_step(observations, rewards, dones, infos)

            assert SOCIAL_AGENT_ID not in observations
            assert SOCIAL_AGENT_ID not in dones

            # Reward is currently the delta in distance travelled by this agent.
            # We want to make sure that this is infact a delta and not total distance
            # travelled since this bug has appeared a few times.
            #
            # The way to verify this is by making sure the reward does not grow without bounds
            assert -3 < rewards[AGENT_ID] < 3

    assert episode.index == (
        MAX_EPISODES - 1
    ), "Simulation must cycle through to the final episode"
