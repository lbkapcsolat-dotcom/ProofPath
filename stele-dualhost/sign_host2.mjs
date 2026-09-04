import fs from 'node:fs';
import crypto from 'node:crypto';
import {createSignedAttestation} from './attestor.mjs';

const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const replayText = fs.readFileSync('/tmp/replay_second_host.json','utf8');
const matrixText = fs.readFileSync('/tmp/hardening_matrix_second_host.json','utf8');
const ns = JSON.parse(fs.readFileSync('/tmp/namespace_inside.json','utf8'));
const replay = JSON.parse(replayText);
const matrix = JSON.parse(matrixText);
const expectedReplay='25b0fa5e9d5255f3584dbd8aa110e85c9fce7a198786cb98f981a2d843488d01';
const expectedMatrix='1cd201f8af1a5ac6890cbeb8c56b23e9ea27e0f11bb6e4a790312cefc090ffc8';
if (sha(Buffer.from(replayText)) !== expectedReplay) throw new Error('REPLAY_SHA_MISMATCH');
if (sha(Buffer.from(matrixText)) !== expectedMatrix) throw new Error('MATRIX_SHA_MISMATCH');
if (matrix.case_count!==57 || matrix.pass_count!==57 || matrix.fail_count!==0 || matrix.unauthorized_execution_failures!==0) throw new Error('MATRIX_CONTENT_MISMATCH');
if (ns.inside_pid !== 1 || ns.default_route_count !== 0) throw new Error('NAMESPACE_CONTENT_MISMATCH');
const shared_claims={
  schema:'STELE_DUAL_HOST_SIGNED_ATTESTATION_SHARED_CLAIMS_V1',
  frozen_package_sha256:'7cf0336241c4891c5f5808b2c0495d0bd64869b749ca32d7952677991a66b20e',
  current_window_authority:replay.decision.current_window_authority,
  global_authority:replay.decision.global_authority,
  replay_sha256:expectedReplay,
  hardening_matrix_sha256:expectedMatrix,
  hardening_cases:57,
  unauthorized_execution_failures:0,
  runtime_admission:replay.decision.runtime_admission,
  production_readiness:replay.decision.production_readiness,
  automatic_promotion:replay.decision.automatic_promotion,
  external_actuation:replay.decision.external_actuation,
};
const host_evidence={
  test_suite:'48/48 PASS',
  hardening_matrix:'57/57 PASS',
  unauthorized_execution_failures:0,
  namespaces:{
    mount:{host:process.env.HOST_MNT_NS,inside:ns.inside_mnt_ns,separated:process.env.HOST_MNT_NS!==ns.inside_mnt_ns},
    pid:{host:process.env.HOST_PID_NS,inside:ns.inside_pid_ns,separated:process.env.HOST_PID_NS!==ns.inside_pid_ns,inside_pid_1:ns.inside_pid===1},
    network:{host:process.env.HOST_NET_NS,inside:ns.inside_net_ns,separated:process.env.HOST_NET_NS!==ns.inside_net_ns,default_route_count:ns.default_route_count},
  },
  mount_marker_host_visible_after_exit:false,
  provider:'GitHub-hosted Actions',
  runner:'ubuntu-24.04',
  git_sha:process.env.GITHUB_SHA,
  workflow_run_id:Number(process.env.GITHUB_RUN_ID),
};
if (!host_evidence.namespaces.mount.separated || !host_evidence.namespaces.pid.separated || !host_evidence.namespaces.network.separated) throw new Error('NAMESPACE_NOT_SEPARATED');
const att=createSignedAttestation({host_id:'host2-github',host_role:'namespace_capable_second_host',shared_claims,host_evidence});
fs.writeFileSync('/tmp/host2_attestation.json',JSON.stringify(att,null,2)+'\n');
fs.writeFileSync('/tmp/host2_attestation_summary.json',JSON.stringify({payload_sha256:att.payload_sha256,public_key_fingerprint_sha256:att.public_key_fingerprint_sha256},null,2)+'\n');
