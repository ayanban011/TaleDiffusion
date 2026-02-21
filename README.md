# TaleDiffusion

## Description
Pytorch implementation of the paper [TaleDiffusion: Multi-Character Story Generation with Dialogue Rendering](https://arxiv.org/abs/2509.04123). This model is implemented on top of the [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) and the [IP-Adapter](https://github.com/tencent-ailab/IP-Adapter).

<p align="center">
  <img src="https://github.com/ayanban011/TaleDiffusion/blob/main/cache/taldiffusion.png">
</p>

## Getting Started

### Step 1: Clone this repository and change the directory to the repository root
```bash
git clone https://github.com/ayanban011/TaleDiffusion.git
cd TaleDiffusion
cd DETECT_SAM
```

### Step 2: Set up the conda environment
```bash
conda create -n talediffusion python=3.9
echo $CUDA_HOME
export CUDA_HOME=/path/to/cuda-11.3
pip install -e .
cd ..
pip install -r requirements.txt
```

### Step 3: downloading the necessary weights
```bash
wget https://huggingface.co/camenduru/YoloWorld-EfficientSAM/resolve/main/efficient_sam_s_gpu.jit -O ./DETECT_SAM/pretrain/efficient_sam_s_gpu.jit
wget https://huggingface.co/alexgenovese/background-workflow/resolve/main/groundingdino_swint_ogc.pth -O ./DETECT_SAM/Grounding-DINO/groundingdino_swint_ogc.pth
wget -c https://huggingface.co/h94/IP-Adapter/resolve/main/models/ip-adapter-plus_sd15.bin -O ./IP-Adapter/models/ip-adapter-plus_sd15.bin
wget -c https://huggingface.co/h94/IP-Adapter/raw/main/models/image_encoder/config.json -O ./IP-Adapter/models/image_encoder/config.json
wget -c https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors -O ./IP-Adapter/models/image_encoder/model.safetensors
```

### Step 4: Run the code
```bash
CUDA_VISIBLE_DEVICES=0 python run.py
```

Make sure you have at least 24GB VRAM in your GPU.

## Citation

If you find this useful for your research, please cite it as follows:
```bash
@misc{banerjee2025talediffusionmulticharacterstorygeneration,
      title={TaleDiffusion: Multi-Character Story Generation with Dialogue Rendering}, 
      author={Ayan Banerjee and Josep Lladós and Umapada Pal and Anjan Dutta},
      year={2025},
      eprint={2509.04123},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2509.04123}, 
}
```

##Acknowledgement

We have built on top of [AutoStudio](https://github.com/donahowe/AutoStudio).

## Conclusion
Thank you for your interest in our work, and sorry if there are any bugs.
