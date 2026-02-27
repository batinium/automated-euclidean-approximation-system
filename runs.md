3.1 -- Field vs Beam baseline (RQ2)
# Beam search baseline
python3 scripts/run_search.py --mode beam --n 7 11 13 --max_depth 3 --max_nodes 15 --beam_width 2000 --dps 80 --run_name "beam_n7-11-13_d3_nodes15_bw2000"

# Field search baseline

python3 scripts/run_search.py --mode field --n 7 11 13 --max_depth 3 --max_height 20 --max_radicand 30 --beam_width 2000 --dps 80 --run_name "field_n7-11-13_d3_h20_r30_bw2000"

3.2 -- Height scaling sweep (RQ1), n=7,13 at depth 2

for H in 8 12 16 24 32 48; do  
    python3 scripts/run_search.py --mode field --n 7 13 --max_depth 2 --max_height "$H" --max_radicand 30 --beam_width 2000 --dps 80 --run_name "field_n7-13_d2_h${H}_r30_bw2000"
done


3.3 -- Depth scaling at h=32 (RQ1/RQ2), n=7,11,13

for D in 0 1 2 3 4; do 
    python3 scripts/run_search.py --mode field --n 7 11 13 --max_depth "$D" --max_height 32 --max_radicand 30 --beam_width 2000 --dps 80 --run_name "field_n7-11-13_d${D}_h32_r30_bw2000"
done

3.5 -- Saturation control at h=64, n=7,11,13
python3 scripts/run_search.py --mode field --n 7 11 13 --max_depth 4 --max_height 64 --max_radicand 30 --beam_width 2000 --dps 80 --run_name "field_n7-11-13_d4_h64_r30_bw2000"

4 -- Regenerate all analysis
python3 scripts/plot_results.py --root results --all-runspython3 scripts/analyse_scaling.py

That's 14 search runs total. Rough time estimates:
Beam baseline: ~30s
Field h=20 baseline: ~80s
Height sweep (6 runs): ~30-80s each depending on height
Depth sweep (5 runs): ~30-80s each depending on depth
Saturation h=64: ~230s (the big one)
Total: roughly 15-20 minutes end to end.