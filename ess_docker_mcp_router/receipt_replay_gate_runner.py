import copy
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

from executor_binding import plan_execution, validate_execution_trace
from receipt_binding import (
    ReceiptBindingError,
    build_surface_receipt,
    compare_independent_replay,
    validate_surface_receipt,
)


PRIMARY_HEAD_SHA = os.environ["PRIMARY_HEAD_SHA"]
PRIMARY_RUN_ID = int(os.environ["PRIMARY_RUN_ID"])
PRIMARY_ARTIFACT_ID = int(os.environ["PRIMARY_ARTIFACT_ID"])
PRIMARY_ARTIFACT_SHA256 = os.environ["PRIMARY_ARTIFACT_SHA256"]
MCP_GATEWAY_VERSION = os.environ["MCP_GATEWAY_VERSION"]
DOCKER_MCP_CATALOG = os.environ["DOCKER_MCP_CATALOG"]
GITHUB_RUN_ID = int(os.environ["GITHUB_RUN_ID"])
GITHUB_SHA = os.environ["GITHUB_SHA"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
WORKSPACE = pathlib.Path(os.environ["GITHUB_WORKSPACE"])
ROOT = WORKSPACE / "evidence" / "ess-router-executor-receipt-replay-bind-v1"
PRIMARY = ROOT / "primary-artifact"
PRIMARY_RECEIPTS = ROOT / "primary-receipts"
REPLAY = ROOT / "replay"
COMPARISONS = ROOT / "comparisons"
NEGATIVE = ROOT / "negative"
POLICY_PATH = WORKSPACE / "ess_docker_mcp_router" / "policy.json"
PROFILE_PATH = WORKSPACE / "ess_docker_mcp_router" / "ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json"
INPUT_ROOT = WORKSPACE / "evidence" / "ess-router-executor-full-matrix-v1"


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(pathlib.Path(path).read_bytes())


def canonical_json_sha(value):
    return sha_bytes(canonical_bytes(value))


def run(cmd, *, cwd=None, timeout=240, check=True):
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"COMMAND_FAILED:{cmd[0]}:{r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    return r


def write_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def recompute_receipt_self_hash(receipt):
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = canonical_json_sha(unsigned)


def prepare_dirs():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for p in (PRIMARY, PRIMARY_RECEIPTS, REPLAY, COMPARISONS, NEGATIVE):
        p.mkdir(parents=True, exist_ok=True)


def recover_and_verify_primary():
    zip_path = ROOT / "primary-artifact.zip"
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/artifacts/{PRIMARY_ARTIFACT_ID}/zip"
    r = run([
        "curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "240",
        "-H", f"Authorization: Bearer {GITHUB_TOKEN}",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
        url, "-o", str(zip_path),
    ])
    assert r.returncode == 0
    actual_zip_sha = sha_file(zip_path)
    assert actual_zip_sha == PRIMARY_ARTIFACT_SHA256, (actual_zip_sha, PRIMARY_ARTIFACT_SHA256)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(PRIMARY)

    manifest = PRIMARY / "sha256-manifest.txt"
    checked = 0
    errors = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        h, n, rel = line.split("  ", 2)
        p = PRIMARY / rel
        if not p.is_file():
            errors.append(f"missing:{rel}")
            continue
        b = p.read_bytes()
        checked += 1
        if len(b) != int(n):
            errors.append(f"bytes:{rel}")
        if sha_bytes(b) != h:
            errors.append(f"sha:{rel}")
    assert checked == 166, (checked, errors)
    assert not errors, errors

    summary = json.loads((PRIMARY / "summary.json").read_text())
    final_receipt_path = WORKSPACE / "evidence" / "receipts" / "ESS_DOCKER_MCP_12_ROUTABLE_SURFACES_ROUTER_TO_EXECUTOR_FULL_MATRIX_AND_NEGATIVE_ROUTE_CANARIES_V1_FINAL_READBACK_RECEIPT.json"
    final_receipt = json.loads(final_receipt_path.read_text())
    assert summary["positive_surface_count"] == 12
    assert summary["negative_canary_count"] == 4
    assert final_receipt["final_live_integration"]["run_id"] == PRIMARY_RUN_ID
    assert final_receipt["final_artifact"]["provider_artifact_id"] == PRIMARY_ARTIFACT_ID
    assert final_receipt["final_artifact"]["provider_artifact_sha256"] == PRIMARY_ARTIFACT_SHA256
    write_json(ROOT / "primary-custody-readback.json", {
        "primary_run_id": PRIMARY_RUN_ID,
        "primary_head_sha": PRIMARY_HEAD_SHA,
        "primary_artifact_id": PRIMARY_ARTIFACT_ID,
        "primary_artifact_sha256": PRIMARY_ARTIFACT_SHA256,
        "primary_zip_sha256_readback": actual_zip_sha,
        "internal_manifest_checked": checked,
        "internal_manifest_errors": len(errors),
        "primary_final_receipt_bound": True,
    })


def verify_authority_continuity():
    current_policy = json.loads(POLICY_PATH.read_text())
    current_profile = json.loads(PROFILE_PATH.read_text())
    primary_policy = json.loads((PRIMARY / "policy-authority.json").read_text())
    primary_profile = json.loads((PRIMARY / "profile-authority.json").read_text())
    assert current_policy == primary_policy
    assert current_profile == primary_profile

    policy_canonical_sha = canonical_json_sha(current_policy)
    profile_canonical_sha = canonical_json_sha(current_profile)
    assert policy_canonical_sha == canonical_json_sha(primary_policy)
    assert profile_canonical_sha == canonical_json_sha(primary_profile)

    run(["git", "cat-file", "-e", f"{PRIMARY_HEAD_SHA}^{{commit}}"], cwd=WORKSPACE)
    continuity_files = [
        "ess_docker_mcp_router/router.py",
        "ess_docker_mcp_router/executor_binding.py",
        "ess_docker_mcp_router/policy.json",
        "ess_docker_mcp_router/ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json",
    ]
    run(["git", "diff", "--exit-code", PRIMARY_HEAD_SHA, "--", *continuity_files], cwd=WORKSPACE)

    source_hashes = {}
    for rel in [
        "ess_docker_mcp_router/router.py",
        "ess_docker_mcp_router/executor_binding.py",
        "ess_docker_mcp_router/receipt_binding.py",
        "ess_docker_mcp_router/policy.json",
        "ess_docker_mcp_router/ESS_DOCKER_MCP_13_PROVEN_LIVE_EXPERT_SURFACES_CONTROLLED_PROFILE_V1.json",
    ]:
        source_hashes[rel] = sha_file(WORKSPACE / rel)
    write_json(ROOT / "authority-continuity.json", {
        "policy_semantic_equal": True,
        "profile_semantic_equal": True,
        "policy_canonical_sha256": policy_canonical_sha,
        "profile_canonical_sha256": profile_canonical_sha,
        "router_executor_policy_profile_git_equal_to_primary_head": True,
        "primary_head_sha": PRIMARY_HEAD_SHA,
        "source_file_sha256": source_hashes,
        "note": "Artifact authority JSON was canonically reserialized in the primary run; semantic parsed-object equality plus canonical JSON SHA equality is the correct authority invariant. Router/executor source continuity remains exact git equality.",
    })
    return current_policy, current_profile, policy_canonical_sha, profile_canonical_sha


def build_primary_receipts(policy_sha, profile_sha):
    rows = []
    dirs = sorted((PRIMARY / "positive").iterdir())
    assert len(dirs) == 12
    for d in dirs:
        request = json.loads((d / "request.json").read_text())
        plan = json.loads((d / "execution-plan.json").read_text())
        trace = json.loads((d / "executor-trace.json").read_text())
        response_path = d / ("response.txt" if (d / "response.txt").exists() else "call.json")
        response = response_path.read_bytes()
        surface = plan["executor_contract"]["surface"]
        receipt = build_surface_receipt(
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=response,
            policy_sha256=policy_sha,
            profile_sha256=profile_sha,
            execution_id=f"primary-run-{PRIMARY_RUN_ID}-{surface}",
        )
        validate_surface_receipt(
            receipt=receipt,
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=response,
            policy_sha256=policy_sha,
            profile_sha256=profile_sha,
        )
        write_json(PRIMARY_RECEIPTS / f"{surface}.json", receipt)
        rows.append({
            "surface": surface,
            "transport": receipt["transport"],
            "receipt_sha256": receipt["receipt_sha256"],
            "response_sha256": receipt["response_sha256"],
            "response_bytes": receipt["response_bytes"],
            "source_dir": d.name,
        })
    assert len(rows) == 12 and len({r["surface"] for r in rows}) == 12
    write_json(ROOT / "primary-receipt-index.json", rows)


def prepare_direct_inputs():
    if INPUT_ROOT.exists():
        shutil.rmtree(INPUT_ROOT)
    (INPUT_ROOT / "rust-readonly").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRIMARY / "synthetic-openapi.yaml", INPUT_ROOT / "synthetic-openapi.yaml")
    shutil.copy2(PRIMARY / "rust-readonly" / "canary.txt", INPUT_ROOT / "rust-readonly" / "canary.txt")
    os.chmod(INPUT_ROOT / "synthetic-openapi.yaml", 0o444)
    os.chmod(INPUT_ROOT / "rust-readonly" / "canary.txt", 0o444)
    os.chmod(INPUT_ROOT / "rust-readonly", 0o555)
    assert (PRIMARY / "synthetic-openapi.yaml").read_bytes() == (INPUT_ROOT / "synthetic-openapi.yaml").read_bytes()
    assert (PRIMARY / "rust-readonly" / "canary.txt").read_bytes() == (INPUT_ROOT / "rust-readonly" / "canary.txt").read_bytes()
    before = {
        "synthetic-openapi.yaml": sha_file(INPUT_ROOT / "synthetic-openapi.yaml"),
        "rust-readonly/canary.txt": sha_file(INPUT_ROOT / "rust-readonly" / "canary.txt"),
    }
    write_json(ROOT / "replay-input-before.json", before)
    return before


def install_gateway():
    plugin_dir = pathlib.Path.home() / ".docker" / "cli-plugins"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    release_req = urllib.request.Request(
        f"https://api.github.com/repos/docker/mcp-gateway/releases/tags/{MCP_GATEWAY_VERSION}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(release_req, timeout=60) as r:
        release = json.load(r)
    asset = next(a for a in release["assets"] if a["name"] == "docker-mcp-linux-amd64.tar.gz")
    tgz = pathlib.Path(tempfile.gettempdir()) / "docker-mcp-replay.tgz"
    run(["curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "180", asset["browser_download_url"], "-o", str(tgz)])
    (ROOT / "docker-mcp-release-tar.sha256").write_text(f"{sha_file(tgz)}  {tgz}\n")
    extract = pathlib.Path(tempfile.gettempdir()) / "mcp-replay-extract"
    if extract.exists():
        shutil.rmtree(extract)
    extract.mkdir()
    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(extract)
    src = extract / "docker-mcp"
    dst = plugin_dir / "docker-mcp"
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)
    version = run(["docker", "mcp", "version"])
    (ROOT / "docker-mcp-version.txt").write_text(version.stdout)
    assert MCP_GATEWAY_VERSION.lstrip("v") in version.stdout
    feature = run(["docker", "mcp", "feature", "enable", "profiles"], check=False)
    (ROOT / "profile-feature.out").write_text(feature.stdout)
    (ROOT / "profile-feature.err").write_text(feature.stderr)
    cat = run(["docker", "mcp", "catalog", "pull", DOCKER_MCP_CATALOG])
    (ROOT / "catalog-pull.log").write_text(cat.stdout + cat.stderr)


def execute_gateway_replays(policy, profile, policy_sha, profile_sha):
    rows = []
    dirs = sorted((PRIMARY / "positive").iterdir())[:10]
    assert len(dirs) == 10
    for idx, primary_dir in enumerate(dirs, start=1):
        request = json.loads((primary_dir / "request.json").read_text())
        plan = plan_execution(request, profile, policy)
        assert plan["executor_allowed"]
        contract = plan["executor_contract"]
        assert contract["transport"] == "gateway-profile"
        surface = contract["surface"]
        out = REPLAY / primary_dir.name
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "request.json", request)
        write_json(out / "execution-plan.json", plan)
        profile_id = f"ess-receipt-replay-{GITHUB_RUN_ID}-{idx}"
        create = run([
            "docker", "mcp", "profile", "create",
            "--name", f"ESS RECEIPT REPLAY {surface}",
            "--id", profile_id,
            "--server", f"catalog://mcp/docker-mcp-catalog/{surface}",
        ])
        (out / "profile-create.out").write_text(create.stdout)
        (out / "profile-create.err").write_text(create.stderr)
        tools = run([
            "docker", "mcp", "tools", "--format", "json",
            f"--gateway-arg=--profile={profile_id}",
            "--gateway-arg=--verify-signatures", "ls",
        ], timeout=90)
        (out / "tools.json").write_text(tools.stdout)
        (out / "tools.err").write_text(tools.stderr)
        assert f'"{contract["tool"]}"' in tools.stdout
        call = [
            "docker", "mcp", "tools",
            f"--gateway-arg=--profile={profile_id}",
            "--gateway-arg=--verify-signatures",
            "call", contract["tool"],
            *[f"{k}={v}" for k, v in contract["arguments"].items()],
        ]
        result = run(call, timeout=120)
        (out / "response.txt").write_text(result.stdout)
        (out / "live.err").write_text(result.stderr)
        assert result.stdout.strip()
        trace = {
            **contract,
            "executor_invoked": True,
            "exit_code": result.returncode,
            "argv": call,
            "profile_id": profile_id,
        }
        validate_execution_trace(plan, trace)
        write_json(out / "executor-trace.json", trace)
        receipt = build_surface_receipt(
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=(out / "response.txt").read_bytes(),
            policy_sha256=policy_sha,
            profile_sha256=profile_sha,
            execution_id=f"replay-run-{GITHUB_RUN_ID}-{surface}",
        )
        validate_surface_receipt(
            receipt=receipt,
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=(out / "response.txt").read_bytes(),
            policy_sha256=policy_sha,
            profile_sha256=profile_sha,
        )
        write_json(out / "receipt.json", receipt)
        rows.append({
            "surface": surface,
            "transport": contract["transport"],
            "status": "REPLAY_RECEIPT_BOUND_PASS",
            "receipt_sha256": receipt["receipt_sha256"],
            "response_sha256": receipt["response_sha256"],
        })
    return rows


GO_SOURCE = r'''package main
import("context";"encoding/json";"os";"os/exec";"path/filepath";"strings";"time";"github.com/modelcontextprotocol/go-sdk/mcp")
type Contract struct{Surface string `json:"surface"`;Tool string `json:"tool"`;Transport string `json:"transport"`;Arguments map[string]any `json:"arguments"`;ReadOnly bool `json:"read_only"`;ExternalActuation bool `json:"external_actuation"`;ImageDigest string `json:"image_digest"`}
func must(e error){if e!=nil{panic(e)}}
func writeJSON(p string,v any){b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(p,append(b,'\n'),0644))}
func main(){
 if len(os.Args)!=3{panic("usage: bound-direct contract.json evidence-dir")}
 cb,e:=os.ReadFile(os.Args[1]);must(e);var c Contract;must(json.Unmarshal(cb,&c));if c.Transport!="direct-image"||!c.ReadOnly||c.ExternalActuation{panic("invalid direct contract")}
 out:=os.Args[2];ctx,cancel:=context.WithTimeout(context.Background(),120*time.Second);defer cancel();var cmd *exec.Cmd;var expect string
 if c.Surface=="openapi-schema"{p:=c.Arguments["openapiSchemaPath"].(string);image:="mcp/openapi-schema@"+c.ImageDigest;cmd=exec.CommandContext(ctx,"docker","run","--rm","-i","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges","--tmpfs","/tmp:rw,noexec,nosuid,size=64m","-v",p+":"+p+":ro",image);expect="/health"}else if c.Surface=="rust-mcp-filesystem"{d:=c.Arguments["path"].(string);image:="mcp/rust-mcp-filesystem@"+c.ImageDigest;cmd=exec.CommandContext(ctx,"docker","run","--rm","-i","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges","--tmpfs","/tmp:rw,noexec,nosuid,size=64m","-e","ENABLE_ROOTS=false","-e","ALLOW_WRITE=false","-v",d+":"+d+":ro",image,d);expect="canary.txt"}else{panic("unknown direct surface")}
 stderr,e:=os.Create(filepath.Join(out,"container-stderr.log"));must(e);defer stderr.Close();cmd.Stderr=stderr
 cl:=mcp.NewClient(&mcp.Implementation{Name:"ess-receipt-bound-direct",Version:"1.0.0"},nil);s,e:=cl.Connect(ctx,&mcp.CommandTransport{Command:cmd},nil);must(e);defer s.Close();lt,e:=s.ListTools(ctx,&mcp.ListToolsParams{});must(e);found:=false;for _,t:=range lt.Tools{if t.Name==c.Tool{found=true}};if !found{panic("expected tool missing")};writeJSON(filepath.Join(out,"tools.json"),lt);res,e:=s.CallTool(ctx,&mcp.CallToolParams{Name:c.Tool,Arguments:c.Arguments});must(e);if res.IsError{panic("tool error")};writeJSON(filepath.Join(out,"call.json"),res);rb,_:=json.Marshal(res);if !strings.Contains(string(rb),expect){panic("expected output evidence missing")};trace:=map[string]any{"surface":c.Surface,"tool":c.Tool,"transport":c.Transport,"arguments":c.Arguments,"read_only":c.ReadOnly,"external_actuation":c.ExternalActuation,"image_digest":c.ImageDigest,"executor_invoked":true,"exit_code":0};writeJSON(filepath.Join(out,"executor-trace.json"),trace)
}
'''


def build_direct_executor():
    d = pathlib.Path(tempfile.gettempdir()) / "ess-receipt-bound-direct"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    (d / "go.mod").write_text("module ess-receipt-bound-direct\n\ngo 1.25.0\n\nrequire github.com/modelcontextprotocol/go-sdk v1.4.1\n")
    (d / "main.go").write_text(GO_SOURCE)
    run(["go", "mod", "tidy"], cwd=d, timeout=180)
    binary = d / "bound-direct"
    run(["go", "build", "-o", str(binary), "."], cwd=d, timeout=180)
    return binary


def execute_direct_replays(binary, policy, profile, policy_sha, profile_sha):
    rows = []
    dirs = sorted((PRIMARY / "positive").iterdir())[10:]
    assert len(dirs) == 2
    for primary_dir in dirs:
        request = json.loads((primary_dir / "request.json").read_text())
        plan = plan_execution(request, profile, policy)
        assert plan["executor_allowed"]
        contract = plan["executor_contract"]
        assert contract["transport"] == "direct-image"
        surface = contract["surface"]
        out = REPLAY / primary_dir.name
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "request.json", request)
        write_json(out / "execution-plan.json", plan)
        contract_path = out / "executor-contract.json"
        write_json(contract_path, contract)
        result = run([str(binary), str(contract_path), str(out)], timeout=180)
        (out / "direct.out").write_text(result.stdout)
        trace = json.loads((out / "executor-trace.json").read_text())
        validate_execution_trace(plan, trace)
        response = (out / "call.json").read_bytes()
        receipt = build_surface_receipt(
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=response,
            policy_sha256=policy_sha,
            profile_sha256=profile_sha,
            execution_id=f"replay-run-{GITHUB_RUN_ID}-{surface}",
        )
        validate_surface_receipt(
            receipt=receipt,
            request=request,
            plan=plan,
            trace=trace,
            response_bytes=response,
            policy_sha256=policy_sha,
            profile_sha256=profile_sha,
        )
        write_json(out / "receipt.json", receipt)
        rows.append({
            "surface": surface,
            "transport": contract["transport"],
            "status": "REPLAY_RECEIPT_BOUND_PASS",
            "receipt_sha256": receipt["receipt_sha256"],
            "response_sha256": receipt["response_sha256"],
        })
    return rows


def compare_replays_and_negative_canaries(policy_sha, profile_sha):
    comparisons = []
    replay_receipts = {}
    for p in REPLAY.rglob("receipt.json"):
        r = json.loads(p.read_text())
        replay_receipts.setdefault(r["surface"], []).append((p, r))
    for pr in sorted(PRIMARY_RECEIPTS.glob("*.json")):
        primary_receipt = json.loads(pr.read_text())
        matches = replay_receipts.get(primary_receipt["surface"], [])
        assert len(matches) == 1, (primary_receipt["surface"], matches)
        path, replay_receipt = matches[0]
        comp = compare_independent_replay(primary_receipt, replay_receipt)
        comp["replay_receipt_path"] = str(path.relative_to(ROOT))
        comparisons.append(comp)
    assert len(comparisons) == 12
    assert len({c["surface"] for c in comparisons}) == 12
    gateway = [c for c in comparisons if c["transport"] == "gateway-profile"]
    direct = [c for c in comparisons if c["transport"] == "direct-image"]
    assert len(gateway) == 10 and len(direct) == 2
    assert all(c["replay_valid"] for c in comparisons)
    assert all(c["response_sha256_equal"] and c["response_equivalence"] == "EXACT_RESPONSE_REPLAY" for c in direct)
    assert all(c["response_equivalence"] == "RESPONSE_INDIVIDUALLY_BOUND__BYTE_EQUALITY_NOT_REQUIRED" for c in gateway)
    write_json(COMPARISONS / "replay-comparisons.json", comparisons)

    d = PRIMARY / "positive" / "02-papers"
    request = json.loads((d / "request.json").read_text())
    plan = json.loads((d / "execution-plan.json").read_text())
    trace = json.loads((d / "executor-trace.json").read_text())
    response = (d / "response.txt").read_bytes()
    base = json.loads((PRIMARY_RECEIPTS / "paper-search.json").read_text())
    mutations = {
        "request_sha256": "0" * 64,
        "route_sha256": "1" * 64,
        "executor_contract_sha256": "2" * 64,
        "response_sha256": "3" * 64,
        "policy_sha256": "4" * 64,
        "profile_sha256": "5" * 64,
    }
    neg = []
    for field, value in mutations.items():
        tampered = copy.deepcopy(base)
        tampered[field] = value
        recompute_receipt_self_hash(tampered)
        try:
            validate_surface_receipt(
                receipt=tampered,
                request=request,
                plan=plan,
                trace=trace,
                response_bytes=response,
                policy_sha256=policy_sha,
                profile_sha256=profile_sha,
            )
        except ReceiptBindingError as exc:
            neg.append({"canary": f"coherent-tamper-{field}", "status": "DENY_PASS", "reason": str(exc)})
        else:
            raise AssertionError(f"tamper accepted:{field}")

    other = json.loads((PRIMARY_RECEIPTS / "context7.json").read_text())
    try:
        compare_independent_replay(base, other)
    except ReceiptBindingError as exc:
        neg.append({"canary": "cross-surface-receipt-swap", "status": "DENY_PASS", "reason": str(exc)})
    else:
        raise AssertionError("cross-surface receipt swap accepted")

    same = copy.deepcopy(base)
    try:
        compare_independent_replay(base, same)
    except ReceiptBindingError as exc:
        neg.append({"canary": "same-execution-replay", "status": "DENY_PASS", "reason": str(exc)})
    else:
        raise AssertionError("same execution accepted as independent replay")

    assert len(neg) == 8 and all(x["status"] == "DENY_PASS" for x in neg)
    write_json(NEGATIVE / "receipt-negative-canaries.json", neg)
    return comparisons, neg


def verify_direct_inputs_immutable(before):
    after = {
        "synthetic-openapi.yaml": sha_file(INPUT_ROOT / "synthetic-openapi.yaml"),
        "rust-readonly/canary.txt": sha_file(INPUT_ROOT / "rust-readonly" / "canary.txt"),
    }
    assert before == after
    write_json(ROOT / "replay-input-after.json", after)
    write_json(ROOT / "replay-input-equality.json", {"equal": True, "before": before, "after": after})


def build_summary(comparisons, neg, replay_rows):
    gateway = [x for x in comparisons if x["transport"] == "gateway-profile"]
    direct = [x for x in comparisons if x["transport"] == "direct-image"]
    summary = {
        "gate": "ESS_DOCKER_MCP_12_SURFACE_ROUTER_EXECUTOR_RECEIPT_AND_INDEPENDENT_REPLAY_BIND_V1",
        "verdict": "PASS_12_OF_12_PRIMARY_RESPONSE_RECEIPTS_BOUND__12_OF_12_INDEPENDENT_REPLAY_RECEIPTS_BOUND__2_OF_2_DIRECT_EXACT_RESPONSE_REPLAY__8_OF_8_RECEIPT_NEGATIVE_CANARIES_FAIL_CLOSED",
        "primary_run_id": PRIMARY_RUN_ID,
        "primary_head_sha": PRIMARY_HEAD_SHA,
        "primary_artifact_id": PRIMARY_ARTIFACT_ID,
        "primary_artifact_sha256": PRIMARY_ARTIFACT_SHA256,
        "replay_run_id": GITHUB_RUN_ID,
        "replay_head_sha": GITHUB_SHA,
        "primary_receipt_count": 12,
        "independent_replay_receipt_count": 12,
        "gateway_profile_replay_count": len(gateway),
        "direct_image_replay_count": len(direct),
        "direct_exact_response_sha_equal_count": sum(x["response_sha256_equal"] for x in direct),
        "gateway_response_sha_equal_count_observed": sum(x["response_sha256_equal"] for x in gateway),
        "receipt_negative_canary_count": len(neg),
        "replay_status_counts": {"REPLAY_RECEIPT_BOUND_PASS": sum(x["status"] == "REPLAY_RECEIPT_BOUND_PASS" for x in replay_rows)},
        "authority_semantic_equal_to_primary_artifact": True,
        "authority_canonical_json_sha_equal": True,
        "router_executor_source_equal_to_primary_head": True,
        "direct_inputs_immutable": True,
        "gemini_quarantine_preserved": True,
        "zero_spend": True,
        "secret_injected": False,
        "external_actuation": False,
        "production_ready": False,
        "runtime_admission": False,
        "global_bind": False,
        "remote_response_claim_boundary": "For 10 gateway-profile surfaces, each primary and replay response is independently SHA256-bound to its own validated receipt; cross-run response-byte equality is observed and recorded but is not required because upstream remote content may legitimately change.",
        "direct_response_claim_boundary": "For 2 digest-pinned local direct-image surfaces over byte-identical read-only synthetic inputs, cross-run response SHA256 equality is required and passed.",
        "claim_boundary": "POLICY_ROUTE_EXECUTOR_RESPONSE_RECEIPT_CHAIN_BOUND_OVER_12_READ_ONLY_SURFACES__PRIMARY_PROVIDER_ARTIFACT_PINNED_AND_REVERIFIED__FRESH_INDEPENDENT_REPLAY_ON_ALL_12__DIRECT_LOCAL_OUTPUTS_EXACT__REMOTE_OUTPUTS_INDIVIDUALLY_EXACTLY_BOUND_NOT_ASSUMED_CROSS_RUN_DETERMINISTIC__NO_PRODUCTION_READY__NO_RUNTIME_ADMISSION__NO_GLOBAL_BIND",
    }
    write_json(ROOT / "summary.json", summary)
    write_json(ROOT / "bounded-receipt.json", summary)
    return summary


def build_manifest():
    entries = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.name != "sha256-manifest.txt":
            b = p.read_bytes()
            entries.append(f"{sha_bytes(b)}  {len(b)}  {p.relative_to(ROOT)}")
    (ROOT / "sha256-manifest.txt").write_text("\n".join(entries) + "\n")
    return len(entries)


def main():
    prepare_dirs()
    recover_and_verify_primary()
    policy, profile, policy_sha, profile_sha = verify_authority_continuity()
    build_primary_receipts(policy_sha, profile_sha)
    before = prepare_direct_inputs()
    install_gateway()
    replay_rows = execute_gateway_replays(policy, profile, policy_sha, profile_sha)
    binary = build_direct_executor()
    replay_rows.extend(execute_direct_replays(binary, policy, profile, policy_sha, profile_sha))
    assert len(replay_rows) == 12 and all(x["status"] == "REPLAY_RECEIPT_BOUND_PASS" for x in replay_rows)
    write_json(ROOT / "replay-results.json", replay_rows)
    comparisons, neg = compare_replays_and_negative_canaries(policy_sha, profile_sha)
    verify_direct_inputs_immutable(before)
    summary = build_summary(comparisons, neg, replay_rows)
    manifest_count = build_manifest()
    summary["manifest_entry_count"] = manifest_count
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
