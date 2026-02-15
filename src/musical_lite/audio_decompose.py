import os, sys, argparse
import pathlib
import tqdm
import torch, torchaudio
from torchaudio.pipelines import HDEMUCS_HIGH_MUSDB

model = HDEMUCS_HIGH_MUSDB.get_model()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
sample_rate = HDEMUCS_HIGH_MUSDB.sample_rate
sources = model.sources
num_sources = len(sources)

def decompose(input_path, output_dir=None, segment_length=10.0, padding_length=10.0, verbose=False):
    input_path = pathlib.Path(input_path)
    if output_dir is None:
        output_dir = input_path.parent / (input_path.stem + '_decomposed')
    else:
        output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f'Loading audio from {input_path}...')

    waveform, sr = torchaudio.load(input_path)
    if sr != sample_rate:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=sample_rate)
        waveform = resampler(waveform)
    waveform = waveform.to(device)
    waveform = waveform.unsqueeze(0)  # Add batch dimension

    total_length = waveform.shape[2]
    segment_samples = int(segment_length * sample_rate)
    padding_samples = int(padding_length * sample_rate)
    output = torch.zeros((1, num_sources, waveform.shape[1], total_length), device=device)

    if verbose:
        print(f'Processing audio in segments of {segment_length} seconds with {padding_length} seconds of padding...')

    with torch.no_grad():
        for start in tqdm.tqdm(range(0, total_length, segment_samples), desc='Processing segments', unit='segment', disable=not verbose, leave=False):
            end = min(start + segment_samples, total_length)
            segment_start = start - padding_samples
            segment_end = end + padding_samples
            if segment_start < 0: # keep segment_start-padding_start == start-padding_samples
                padding_start = -segment_start
                segment_start = 0
            else:
                padding_start = 0
            if segment_end > total_length: # likewise, keep segment_end+padding_end == end+padding_samples
                padding_end = segment_end - total_length
                segment_end = total_length
            else:
                padding_end = 0
            segment = waveform[:, :, segment_start:segment_end]
            if padding_start > 0 or padding_end > 0:
                segment = torch.nn.functional.pad(segment, (padding_start, padding_end))
            separated = model(segment)
            output[:, :, :, start:end] = separated[:, :, :, padding_samples:padding_samples + (end - start)]

    if verbose:
        print('Saving decomposed sources...')

    output = output.squeeze(0).cpu()
    for i, source in enumerate(tqdm.tqdm(sources, desc='Saving sources', unit='source', disable=not verbose, leave=False)):
        source_waveform = output[i]
        output_path = output_dir / f'{input_path.stem}_{source}.wav'
        torchaudio.save(output_path, source_waveform, sample_rate)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decompose an audio file into its sources using HDEMUCS.')
    parser.add_argument('input_path', type=str, help='Path to the input audio file.')
    parser.add_argument('-o', '--output_dir', type=str, default=None, help='Directory to save the decomposed sources. Defaults to a subdirectory named after the input file.')
    parser.add_argument('--segment_length', type=float, default=10.0, help='Length of each segment in seconds. Default is 10 seconds.')
    parser.add_argument('--padding_length', type=float, default=10.0, help='Length of padding on each side of the segment in seconds. Default is 10 second.')
    parser.add_argument('--quiet', action='store_true', help='Disable verbose output.')
    args = parser.parse_args()

    decompose(args.input_path, args.output_dir, args.segment_length, args.padding_length, not args.quiet)
                

    

    
