weight = '/mnt/data/OpenAvatarChat/models/LAM_audio2exp/pretrained_models/lam_audio2exp_streaming.tar'
ex_vol = True
audio_input = './assets/sample_audio/BarackObama.wav'
save_json_path = 'bsData.json'
audio_sr = 16000
fps = 30.0
movement_smooth = False
brow_movement = False
id_idx = 0
resume = False
evaluate = True
test_only = False
seed = 8886501
save_path = 'exp/audio2exp'
num_worker = 16
batch_size = 16
batch_size_val = None
batch_size_test = None
epoch = 100
eval_epoch = 100
sync_bn = False
enable_amp = False
empty_cache = False
find_unused_parameters = False
mix_prob = 0
param_dicts = None
model = dict(
    type='DefaultEstimator',
    backbone=dict(
        type='Audio2Expression',
        pretrained_encoder_type='wav2vec',
        pretrained_encoder_path=
        '/mnt/data/OpenAvatarChat/models/wav2vec2-base-960h',
        wav2vec2_config_path=
        '/mnt/data/OpenAvatarChat/src/handlers/avatar/lam/LAM_Audio2Expression/configs/wav2vec2_config.json',
        num_identity_classes=12,
        identity_feat_dim=64,
        hidden_dim=512,
        expression_dim=52,
        norm_type='ln',
        use_transformer=False,
        num_attention_heads=8,
        num_transformer_layers=6),
    criteria=[dict(type='L1Loss', loss_weight=1.0, ignore_index=-1)])
dataset_type = 'audio2exp'
data_root = './'
data = dict(
    train=dict(
        type='audio2exp',
        split='train',
        data_root='./',
        test_mode=False,
        loop=1),
    val=dict(type='audio2exp', split='val', data_root='./', test_mode=False),
    test=dict(type='audio2exp', split='val', data_root='./', test_mode=True))
hooks = [
    dict(type='CheckpointLoader'),
    dict(type='IterationTimer', warmup_iter=2),
    dict(type='InformationWriter'),
    dict(type='SemSegEvaluator'),
    dict(type='CheckpointSaver', save_freq=None),
    dict(type='PreciseEvaluator', test_last=False)
]
train = dict(type='DefaultTrainer')
infer = dict(type='Audio2ExpressionInfer', verbose=True)
