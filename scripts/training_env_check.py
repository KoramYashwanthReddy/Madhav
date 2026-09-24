"""CLI diagnostic utility for inspecting host AI training hardware and framework dependencies."""

import sys
from max.training.hardware import HardwareDetectionService


def check_training_environment() -> None:
    """Print detailed hardware and framework dependency diagnostic report."""
    print("==================================================")
    print("MAX Platform AI Training Environment Check")
    print("==================================================")

    hw_svc = HardwareDetectionService()
    profile = hw_svc.get_hardware_profile()

    print(f"Host OS:                   {profile.os_name}")
    print(f"CPU Cores:                 {profile.cpu_cores}")
    print(f"System RAM (Total/Free):   {profile.ram_total_gb} GB / {profile.ram_free_gb} GB")
    print(f"PyTorch Version:           {profile.pytorch_version}")
    print(f"PyTorch CUDA Support:      {profile.pytorch_cuda_available}")
    print(f"GPU Hardware Detected:     {profile.gpu_available}")
    if profile.gpu_available:
        print(f"GPU Model:                 {profile.gpu_name}")
        print(f"VRAM (Total/Free):         {profile.vram_total_mb} MB / {profile.vram_free_mb} MB")
        print(f"CUDA Driver Version:       {profile.cuda_version}")
    else:
        print("GPU Status:                CPU Execution Engine Only")

    print("\n--------------------------------------------------")
    print("Framework Dependencies Availability:")
    for lib_name in ("transformers", "datasets", "peft", "trl", "accelerate", "bitsandbytes", "safetensors"):
        try:
            mod = __import__(lib_name)
            ver = getattr(mod, "__version__", "installed")
            print(f"  {lib_name:<16}: YES ({ver})")
        except ImportError:
            print(f"  {lib_name:<16}: NO (Not installed)")
    print("--------------------------------------------------")


if __name__ == "__main__":
    check_training_environment()
