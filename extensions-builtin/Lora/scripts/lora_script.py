import torch
import gradio as gr
from fastapi import FastAPI

import lora
import extra_networks_lora
import ui_extra_networks_lora
from modules import script_callbacks, ui_extra_networks, extra_networks, shared

def unload():
    torch.nn.Linear.forward = torch.nn.Linear_forward_before_lora
    torch.nn.Linear._load_from_state_dict = torch.nn.Linear_load_state_dict_before_lora
    torch.nn.Conv2d.forward = torch.nn.Conv2d_forward_before_lora
    torch.nn.Conv2d._load_from_state_dict = torch.nn.Conv2d_load_state_dict_before_lora
    torch.nn.MultiheadAttention.forward = torch.nn.MultiheadAttention_forward_before_lora
    torch.nn.MultiheadAttention._load_from_state_dict = torch.nn.MultiheadAttention_load_state_dict_before_lora


def before_ui():
    ui_extra_networks.register_page(ui_extra_networks_lora.ExtraNetworksPageLora())
    extra_networks.register_extra_network(extra_networks_lora.ExtraNetworkLora())

if not hasattr(torch.nn, 'Linear_forward_before_lora'):
    torch.nn.Linear_forward_before_lora = torch.nn.Linear.forward

if not hasattr(torch.nn, 'Linear_load_state_dict_before_lora'):
    torch.nn.Linear_load_state_dict_before_lora = torch.nn.Linear._load_from_state_dict

if not hasattr(torch.nn, 'Conv2d_forward_before_lora'):
    torch.nn.Conv2d_forward_before_lora = torch.nn.Conv2d.forward

if not hasattr(torch.nn, 'Conv2d_load_state_dict_before_lora'):
    torch.nn.Conv2d_load_state_dict_before_lora = torch.nn.Conv2d._load_from_state_dict

if not hasattr(torch.nn, 'MultiheadAttention_forward_before_lora'):
    torch.nn.MultiheadAttention_forward_before_lora = torch.nn.MultiheadAttention.forward

if not hasattr(torch.nn, 'MultiheadAttention_load_state_dict_before_lora'):
    torch.nn.MultiheadAttention_load_state_dict_before_lora = torch.nn.MultiheadAttention._load_from_state_dict

torch.nn.Linear.forward = lora.lora_Linear_forward
torch.nn.Linear._load_from_state_dict = lora.lora_Linear_load_state_dict
torch.nn.Conv2d.forward = lora.lora_Conv2d_forward
torch.nn.Conv2d._load_from_state_dict = lora.lora_Conv2d_load_state_dict
torch.nn.MultiheadAttention.forward = lora.lora_MultiheadAttention_forward
torch.nn.MultiheadAttention._load_from_state_dict = lora.lora_MultiheadAttention_load_state_dict

script_callbacks.on_model_loaded(lora.assign_lora_names_to_compvis_modules)
script_callbacks.on_script_unloaded(unload)
script_callbacks.on_before_ui(before_ui)
script_callbacks.on_infotext_pasted(lora.infotext_pasted)


shared.options_templates.update(shared.options_section(('extra_networks', "Extra Networks"), {
    "sd_lora": shared.OptionInfo("None", "Add Lora to prompt", gr.Dropdown, lambda: {"choices": ["None"] + [x for x in lora.available_loras]}, refresh=lora.list_available_loras),
    "lora_preferred_name": shared.OptionInfo("Alias from file", "When adding to prompt, refer to lora by", gr.Radio, {"choices": ["Alias from file", "Filename"]}),
    "lora_functional": shared.OptionInfo(False, "Lora: use old method that takes longer when you have multiple Loras active and produces same results as kohya-ss/sd-webui-additional-networks extension"),
}))


def create_lora_json(obj: lora.LoraOnDisk):
    return {
        "name": obj.name,
        "alias": obj.alias,
        "path": obj.filename,
        "metadata": obj.metadata,
    }


def api_loras(_: gr.Blocks, app: FastAPI):
    @app.get("/sdapi/v1/loras")
    async def get_loras():
        return [create_lora_json(obj) for obj in lora.available_loras.values()]


script_callbacks.on_app_started(api_loras)

