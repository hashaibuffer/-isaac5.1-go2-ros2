import os
import torch
import carb
import gymnasium as gym
from isaaclab.envs import ManagerBasedEnv
from go2.go2_ctrl_cfg import unitree_go2_flat_cfg, unitree_go2_rough_cfg
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, RslRlOnPolicyRunnerCfg
from isaaclab_tasks.utils import get_checkpoint_path
from rsl_rl.runners import OnPolicyRunner

base_vel_cmd_input = None
selected_robot = 0

def init_base_vel_cmd(num_envs):
    global base_vel_cmd_input
    base_vel_cmd_input = torch.zeros((num_envs, 3), dtype=torch.float32)

def base_vel_cmd(env: ManagerBasedEnv) -> torch.Tensor:
    global base_vel_cmd_input
    return base_vel_cmd_input.clone().to(env.device)

def sub_keyboard_event(event) -> bool:
    global base_vel_cmd_input, selected_robot
    lin_vel = 1.5
    ang_vel = 1.5

    if base_vel_cmd_input is not None:
        key_name = event.input.name.upper() if hasattr(event.input, 'name') else ''

        # Number keys 1-9 or F1-F12 select robots
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            select_map = {
                '1':0, '2':1, '3':2, '4':3, '5':4, '6':5, '7':6, '8':7, '9':8,
                'KEY_1':0, 'KEY_2':1, 'KEY_3':2, 'KEY_4':3, 'KEY_5':4,
                'KEY_6':5, 'KEY_7':6, 'KEY_8':7, 'KEY_9':8,
                'F1':0, 'F2':1, 'F3':2, 'F4':3, 'F5':4, 'F6':5,
                'F7':6, 'F8':7, 'F9':8, 'F10':9, 'F11':10, 'F12':11,
            }
            if key_name in select_map:
                idx = select_map[key_name]
                if idx < base_vel_cmd_input.shape[0]:
                    base_vel_cmd_input.zero_()
                    selected_robot = idx
                    print(f"\r[CONTROL] Robot {selected_robot} selected", end='', flush=True)
                    return True

        # Movement on KEY_PRESS and KEY_REPEAT
        if event.type in (carb.input.KeyboardEventType.KEY_PRESS, carb.input.KeyboardEventType.KEY_REPEAT):
            if key_name == 'W':
                base_vel_cmd_input[selected_robot] = torch.tensor([lin_vel, 0, 0], dtype=torch.float32)
            elif key_name == 'S':
                base_vel_cmd_input[selected_robot] = torch.tensor([-lin_vel, 0, 0], dtype=torch.float32)
            elif key_name == 'A':
                base_vel_cmd_input[selected_robot] = torch.tensor([0, lin_vel, 0], dtype=torch.float32)
            elif key_name == 'D':
                base_vel_cmd_input[selected_robot] = torch.tensor([0, -lin_vel, 0], dtype=torch.float32)
            elif key_name == 'Z':
                base_vel_cmd_input[selected_robot] = torch.tensor([0, 0, ang_vel], dtype=torch.float32)
            elif key_name == 'C':
                base_vel_cmd_input[selected_robot] = torch.tensor([0, 0, -ang_vel], dtype=torch.float32)

        # Stop all on KEY_RELEASE
        elif event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            base_vel_cmd_input.zero_()
    return True

def _get_ckpt_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ckpt_dir = os.path.join(script_dir, "..", "ckpts")
    return os.path.abspath(ckpt_dir)

def get_rsl_flat_policy(cfg):
    cfg.observations.policy.height_scan = None
    env = gym.make("Isaac-Velocity-Flat-Unitree-Go2-v0", cfg=cfg)
    env = RslRlVecEnvWrapper(env)
    agent_cfg: RslRlOnPolicyRunnerCfg = unitree_go2_flat_cfg
    ckpt_path = get_checkpoint_path(log_path=_get_ckpt_path(),
                                    run_dir=agent_cfg["load_run"],
                                    checkpoint=agent_cfg["load_checkpoint"])
    ppo_runner = OnPolicyRunner(env, agent_cfg, log_dir=None, device=agent_cfg["device"])
    ppo_runner.load(ckpt_path)
    policy = ppo_runner.get_inference_policy(device=agent_cfg["device"])
    return env, policy

def get_rsl_rough_policy(cfg):
    env = gym.make("Isaac-Velocity-Rough-Unitree-Go2-v0", cfg=cfg)
    env = RslRlVecEnvWrapper(env)
    agent_cfg: RslRlOnPolicyRunnerCfg = unitree_go2_rough_cfg
    ckpt_path = get_checkpoint_path(log_path=_get_ckpt_path(),
                                    run_dir=agent_cfg["load_run"],
                                    checkpoint=agent_cfg["load_checkpoint"])
    ppo_runner = OnPolicyRunner(env, agent_cfg, log_dir=None, device=agent_cfg["device"])
    ppo_runner.load(ckpt_path)
    policy = ppo_runner.get_inference_policy(device=agent_cfg["device"])
    return env, policy
