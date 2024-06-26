import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks.early_stopping import EarlyStopping

from absa_gnn.models import Model
from absa_gnn.loaders import GraphDataModule

from config import configuration as cfg
# from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

# parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
# parser.add_argument('--TRAIN', type=bool, required=False, default=1, help='Switch to train on dataset')

# args = parser.parse_args()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Ensure Reproducibility ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pl.seed_everything(cfg['training']['seed'])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Initialize Datamodule ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dm = GraphDataModule()

# OPTIONAL
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Logger initialization ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

logger = pl.loggers.TensorBoardLogger("lightning_logs", name=cfg['data']['dataset']['name'])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Model initialization ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

model = Model(in_dim=cfg['model']['in_dim'], hidden_dim=cfg['model']['hidden_dim'], out_dim=cfg['model']['out_dim'],
              num_heads=cfg['model']['num_heads'], num_classes=dm.num_classes, large_graph=dm.large_graph)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Trainer Initialization ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

early_stop_callback = EarlyStopping(
    monitor='val_f1_score',
    min_delta=cfg['training']['early_stopping_delta'],
    patience=cfg['training']['early_stopping_patience'],
    verbose=True,
    mode='max'
    )

cuda_available = torch.cuda.is_available()
n_gpu = torch.cuda.device_count()

if cuda_available:
    accelerator = 'ddp2'
else:
    accelerator = None

trainer = pl.Trainer(max_epochs=cfg['training']['epochs'], log_every_n_steps=50, auto_scale_batch_size='binsearch',
                     gpus=n_gpu, auto_select_gpus=cuda_available, accelerator=accelerator, auto_lr_find=True, fast_dev_run=False,
                     num_sanity_val_steps=0, callbacks=[early_stop_callback], deterministic=True, logger=logger)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Train your model ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

trainer.fit(model, dm)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Test your model ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

trainer.test(datamodule=dm)
