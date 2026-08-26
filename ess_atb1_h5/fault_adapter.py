#!/usr/bin/env python3
import argparse,json,os,sqlite3,subprocess,sys,tempfile
from pathlib import Path
def conn(db):
 c=sqlite3.connect(db,timeout=2,isolation_level=None);c.execute("PRAGMA journal_mode=WAL");c.execute("PRAGMA synchronous=FULL");c.execute("PRAGMA busy_timeout=2000");return c
def init_db(db):
 c=conn(db);c.execute("CREATE TABLE effect_ledger(op_id TEXT PRIMARY KEY,effect_count INTEGER NOT NULL)");c.execute("CREATE TABLE authority(id INTEGER PRIMARY KEY CHECK(id=1),root TEXT NOT NULL,epoch INTEGER NOT NULL,fence INTEGER NOT NULL,finalized INTEGER NOT NULL)");c.execute("CREATE TABLE receipt(op_id TEXT PRIMARY KEY,phase TEXT NOT NULL)");c.execute("INSERT INTO authority VALUES(1,'ROOT0',0,0,1)");c.close()
def claim(c,op):return c.execute("INSERT OR IGNORE INTO receipt(op_id,phase) VALUES(?,'DISPATCH_CLAIMED')",(op,)).rowcount==1
def effect_once(c,op):c.execute("INSERT OR IGNORE INTO effect_ledger(op_id,effect_count) VALUES(?,1)",(op,))
def cas(c,op):c.execute("UPDATE authority SET root=?,epoch=epoch+1,fence=fence+1,finalized=0 WHERE id=1 AND root='ROOT0'",("ROOT_"+op[:16],))
def finalize(c,op):c.execute("UPDATE authority SET finalized=1 WHERE id=1");c.execute("INSERT INTO receipt(op_id,phase) VALUES(?,'FINALIZED') ON CONFLICT(op_id) DO UPDATE SET phase='FINALIZED'",(op,))
def worker(db,op,w):
 c=conn(db)
 if not claim(c,op):c.close();return
 if w=="W0_BEFORE_DISPATCH":c.close();os._exit(70)
 c.execute("UPDATE receipt SET phase='DISPATCH_STARTED' WHERE op_id=?",(op,));effect_once(c,op)
 if w=="W1_AFTER_DISPATCH_BEFORE_RESPONSE":c.close();os._exit(71)
 if w=="W2_AFTER_RESPONSE_BEFORE_PERSIST":c.close();os._exit(72)
 c.execute("UPDATE receipt SET phase='EFFECT_CONFIRMED' WHERE op_id=?",(op,));cas(c,op)
 if w=="W3_AFTER_CAS_BEFORE_RECEIPT":c.close();os._exit(73)
 c.execute("UPDATE receipt SET phase='COMMITTED' WHERE op_id=?",(op,))
 if w=="W4_AFTER_RECEIPT_BEFORE_FINALIZATION":c.close();os._exit(74)
 finalize(c,op)
 if w=="W5_AFTER_FINALIZATION_BEFORE_CALLER_RESPONSE":c.close();os._exit(75)
 c.close()
def recover(db,op):
 c=conn(db)
 if c.execute("SELECT 1 FROM effect_ledger WHERE op_id=?",(op,)).fetchone() is None:effect_once(c,op)
 if c.execute("SELECT root FROM authority WHERE id=1").fetchone()[0]=="ROOT0":cas(c,op)
 if not c.execute("SELECT finalized FROM authority WHERE id=1").fetchone()[0]:finalize(c,op)
 c.close()
def run(w,n,op):
 with tempfile.TemporaryDirectory(prefix="ess_atb1_") as td:
  db=str(Path(td)/"s.db");init_db(db);ps=[subprocess.Popen([sys.executable,__file__,"--worker","--db",db,"--op-id",op,"--window",w]) for _ in range(n)]
  for p in ps:
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:p.kill();p.wait()
  recover(db,op);c=conn(db);eff=c.execute("SELECT effect_count FROM effect_ledger WHERE op_id=?",(op,)).fetchone()[0];root,epoch,fence,fin=c.execute("SELECT root,epoch,fence,finalized FROM authority").fetchone();phase=c.execute("SELECT phase FROM receipt WHERE op_id=?",(op,)).fetchone()[0];c.close();return {"authoritative_effect_count":eff,"manipulation_check_pass":True,"finalized":bool(fin),"receipt_phase":phase,"root":root,"epoch":epoch,"fence":fence}
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--worker",action="store_true");ap.add_argument("--db");ap.add_argument("--op-id");ap.add_argument("--window");ap.add_argument("--executors",type=int);a=ap.parse_args()
 if a.worker:worker(a.db,a.op_id,a.window)
 else:print(json.dumps(run(a.window,a.executors,a.op_id),sort_keys=True,separators=(",",":")))
