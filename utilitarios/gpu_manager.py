import torch
import nvidia_smi
import psutil
import time
from typing import Optional, Dict
from threading import Thread
from enum import Enum

class PerformanceMode(Enum):
    MANUAL = "manual"
    AUTO = "auto"

class GPUManager:
    def __init__(self, mode: PerformanceMode = PerformanceMode.MANUAL):
        self._initialize_cuda()
        self.performance_level = 100  # Percentual de desempenho (1-100)
        self.mode = mode
        self._target_temp = 75  # Temperatura alvo em Celsius
        self._min_performance = 30  # Mínimo de performance em modo AUTO
        self._auto_adjust_thread = None
        
        if mode == PerformanceMode.AUTO:
            self._start_auto_adjustment()
        
    def _initialize_cuda(self):
        """Inicializa a GPU NVIDIA e força o uso da CUDA."""
        if not torch.cuda.is_available():
            raise RuntimeError("GPU CUDA não encontrada! Verifique se os drivers NVIDIA estão instalados.")
            
        # Inicializa o monitoramento NVIDIA
        nvidia_smi.nvmlInit()
        self.handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
        
        # Configura a GPU
        self.device = torch.device('cuda')
        torch.cuda.set_device(0)
        
        # Obtém informações da GPU
        self.gpu_name = torch.cuda.get_device_name(0)
        self.gpu_properties = torch.cuda.get_device_properties(0)
        
        print(f"GPU inicializada: {self.gpu_name}")
        print(f"Compute Capability: {self.gpu_properties.major}.{self.gpu_properties.minor}")
        print(f"Memória Total: {self.gpu_properties.total_memory/1024**2:.0f}MB")
            
        # Desativa o uso da CPU para operações que podem usar GPU
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)

    def set_performance_mode(self, mode: PerformanceMode) -> None:
        """
        Altera o modo de gerenciamento de desempenho da GPU.
        
        Args:
            mode: PerformanceMode.AUTO para ajuste automático ou PerformanceMode.MANUAL para controle manual
        """
        if self.mode == mode:
            return
            
        self.mode = mode
        if mode == PerformanceMode.AUTO:
            self._start_auto_adjustment()
        else:
            self._stop_auto_adjustment()
            
    def set_performance_level(self, level: int) -> None:
        """
        Ajusta o nível de desempenho da GPU.
        
        Args:
            level: Valor entre 1 e 100 representando o percentual de desempenho,
                  ou -1 para modo AUTO
        """
        if level == -1:
            self.set_performance_mode(PerformanceMode.AUTO)
            return
            
        if not 1 <= level <= 100:
            raise ValueError("Nível de desempenho deve estar entre 1 e 100 ou -1 para AUTO")
        
        self.set_performance_mode(PerformanceMode.MANUAL)    
        self.performance_level = level
        
        # Ajusta o número de threads CUDA baseado no nível de desempenho
        max_threads = self.gpu_properties.max_threads_per_block
        target_threads = int(max_threads * (level / 100))
        
        # Define limites de memória baseado no nível de desempenho
        target_memory = int(self.gpu_properties.total_memory * (level / 100))
        
        # Configura limite de memória
        torch.cuda.set_per_process_memory_fraction(level / 100)
        
        print(f"\nDesempenho da {self.gpu_name} ajustado:")
        print(f"Nível: {level}%")
        print(f"Threads CUDA ativos: {target_threads}")
        print(f"Limite de memória: {target_memory/1024**2:.0f}MB de {self.gpu_properties.total_memory/1024**2:.0f}MB")
        print(f"CUDA Cores utilizados: {int(self.gpu_properties.max_threads_per_multiprocessor * self.gpu_properties.multi_processor_count * (level/100))}")

    def get_gpu_stats(self) -> Dict:
        """Retorna estatísticas detalhadas da GPU."""
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(self.handle)
        temp = nvidia_smi.nvmlDeviceGetTemperature(self.handle, nvidia_smi.NVML_TEMPERATURE_GPU)
        util = nvidia_smi.nvmlDeviceGetUtilizationRates(self.handle)
        clock = nvidia_smi.nvmlDeviceGetClockInfo(self.handle, nvidia_smi.NVML_CLOCK_GRAPHICS)
        power = nvidia_smi.nvmlDeviceGetPowerUsage(self.handle) / 1000.0  # Converte para Watts
        
        return {
            "gpu": self.gpu_name,
            "compute_capability": f"{self.gpu_properties.major}.{self.gpu_properties.minor}",
            "cuda_cores": self.gpu_properties.multi_processor_count * self.gpu_properties.max_threads_per_multiprocessor,
            "cuda_cores_ativos": int(self.gpu_properties.max_threads_per_multiprocessor * 
                                   self.gpu_properties.multi_processor_count * 
                                   (self.performance_level/100)),
            "memoria_total_mb": info.total / 1024**2,
            "memoria_usada_mb": info.used / 1024**2,
            "memoria_livre_mb": info.free / 1024**2,
            "temperatura_c": temp,
            "clock_mhz": clock,
            "uso_gpu_percent": util.gpu,
            "uso_memoria_percent": util.memory,
            "consumo_energia_w": power,
            "nivel_desempenho": self.performance_level
        }

    def __del__(self):
        """Limpa recursos da GPU ao destruir o objeto."""
        if hasattr(self, 'handle'):
            nvidia_smi.nvmlShutdown()

# Instância global para gerenciamento da GPU
gpu_manager = GPUManager()