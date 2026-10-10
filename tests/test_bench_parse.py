import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import bench_parse as bp

HDR = "build_commit,build_number,n_threads,type_k,type_v,n_prompt,n_gen,n_depth,avg_ts,stddev_ts"
def test_csv_by_name_any_order():
    a = HDR + '\n"x","11541","2","f16","f16","0","32","0","8.43","0.06"'
    cols = HDR.split(","); cols.reverse()
    vals = ["x", "11541", "2", "f16", "f16", "0", "32", "0", "8.43", "0.06"]; vals.reverse()
    b = ",".join(cols) + "\n" + ",".join('"%s"' % v for v in vals)
    assert bp.summarize(a) == bp.summarize(b)
    assert bp.summarize(a)[0].startswith("test=tg32 ts=8.43+-0.06")

def test_json_and_depth():
    j = '[{"n_prompt":512,"n_gen":0,"n_depth":1024,"avg_ts":32.4,"stddev_ts":0.4,"n_threads":2}]'
    assert bp.summarize(j)[0].startswith("test=pp512@d1024 ts=32.40+-0.40")

def test_ignores_log_lines():
    a = "load_backend: loaded CPU\n" + HDR + '\n"x","1","4","q8_0","q8_0","256","0","0","30.5","1.0"'
    assert bp.summarize(a)[0].startswith("test=pp256 ")
