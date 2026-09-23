import os
import platform
import sys

from pydantic import BaseModel, Field


class ModelRequirements(BaseModel):
    """Resource and environment metadata required by a model."""

    minimum_ram_gb: float = Field(default=1.0, description="Minimum system RAM in GB", ge=0.0)
    recommended_ram_gb: float = Field(
        default=2.0, description="Recommended system RAM in GB", ge=0.0
    )
    minimum_vram_gb: float = Field(default=0.0, description="Minimum GPU VRAM in GB", ge=0.0)
    recommended_vram_gb: float = Field(
        default=0.0, description="Recommended GPU VRAM in GB", ge=0.0
    )
    cpu_required: bool = Field(default=True, description="Can execute on CPU")
    gpu_required: bool = Field(default=False, description="Requires dedicated GPU accelerator")
    supported_gpu_vendor: str | None = Field(
        default=None, description="Optional target GPU vendor (e.g. nvidia, amd, apple)"
    )
    context_length: int = Field(
        default=4096, description="Maximum supported context token length", gt=0
    )
    parameter_count: str | None = Field(
        default=None, description="Parameter scale descriptor (e.g. '7B', '8B')"
    )


class HardwareProfile(BaseModel):
    """Snapshot of current host hardware environment."""

    operating_system: str = Field(description="Operating system name")
    architecture: str = Field(description="System CPU architecture")
    cpu_count: int = Field(description="Number of logical CPU cores")
    system_memory_gb: float = Field(description="Total system RAM in GB")
    gpu_available: bool = Field(default=False, description="GPU hardware accelerator available")
    gpu_vendor: str | None = Field(default=None, description="Detected GPU vendor name")
    gpu_memory_gb: float = Field(default=0.0, description="Detected GPU memory in GB")

    @classmethod
    def detect(cls) -> "HardwareProfile":
        """Detect current host hardware configuration safely using Python standard library."""
        os_name = platform.system()
        arch = platform.machine()
        cpus = os.cpu_count() or 1
        total_ram_gb = 8.0

        try:
            if sys.platform == "win32":
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_ram_gb = round(stat.ullTotalPhys / (1024**3), 2)
            elif hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names:
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                total_ram_gb = round((pages * page_size) / (1024**3), 2)
        except Exception:
            total_ram_gb = 8.0

        return cls(
            operating_system=os_name,
            architecture=arch,
            cpu_count=cpus,
            system_memory_gb=total_ram_gb,
            gpu_available=False,
            gpu_vendor=None,
            gpu_memory_gb=0.0,
        )
