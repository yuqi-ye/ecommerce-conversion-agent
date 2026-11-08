"""在本机终端运行：python agent/run_compare.py --week 2020-12-21"""
import argparse
from datetime import datetime, timezone
from getpass import getpass
import json
from pathlib import Path
import sys
import pymysql
from analysis_tools import validate_week, compare_weeks
from diagnostics import get_source_device_breakdown

ROOT = Path(__file__).resolve().parents[1]

def run_query(password, week, port=3306, details=False):
    connection = pymysql.connect(
        host="127.0.0.1", port=port, user="ecommerce_agent", password=password,
        database="ecommerce_analysis", charset="utf8mb4", autocommit=True,
        connect_timeout=10, read_timeout=65, write_timeout=10,
        local_infile=False,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION max_execution_time = 60000")
            cursor.execute("SET SESSION time_zone = '+00:00'")
            cursor.execute("START TRANSACTION READ ONLY")
        result = compare_weeks(connection, week)
        if details:
            result["diagnostics"] = get_source_device_breakdown(connection, week, result)
        return result
    finally:
        # 不重连；关闭连接释放只读事务，无业务写入。
        connection.close()

def main():
    parser=argparse.ArgumentParser(description="查询目标首访周与前一周，账号为本机 ecommerce_agent。")
    parser.add_argument("--week", default="2020-12-21")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--details", action="store_true", help="同时查询来源、设备、结构分解及筛选对照")
    args=parser.parse_args()
    try:
        validate_week(args.week)
        if not 1 <= args.port <= 65535:
            raise ValueError("端口必须在1至65535之间。")
    except ValueError as exc:
        print(str(exc),file=sys.stderr);return 2
    if not sys.stdin.isatty():
        print("请在本机终端交互运行，密码不通过命令行参数或文件传入。",file=sys.stderr);return 2
    try:
        password=getpass("请输入 ecommerce_agent 账号的密码（输入时不显示字符）：")
        result=run_query(password,args.week,args.port,details=args.details)
        del password
    except (EOFError,KeyboardInterrupt):
        print("\n已取消。",file=sys.stderr);return 130
    except pymysql.MySQLError as exc:
        code=exc.args[0] if exc.args else "unknown"
        tips={
            1045:"账号、密码或本机账号匹配失败，请核对SQL15和本地密码。",
            2003:"无法连接本机MySQL，请确认服务已启动，端口与DataGrip一致。",
            1142:"账号没有视图查询权限，请核对SQL15的GRANT。",
            1356:"视图或其定义者权限异常，请保留错误码反馈。",
            3024:"查询超过60秒，请反馈执行时间，先排查性能。",
        }
        print(f"MySQL错误码：{code}。"+tips.get(code,"请把错误码发给Codex；不要发送密码。"),file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"结果核对失败：{exc}",file=sys.stderr);return 1
    print("\nPython 已从 MySQL 取得结果：")
    for label in ["previous","current"]:
        row=result[label]
        print(f'{row["cohort_week"]}  新访客 {row["new_users"]:,}  7日购买 {row["buyers_7d"]:,}  购买率 {row["conversion_rate"]:.4%}')
    print(f'购买人数变化：{result["change"]["buyers_7d"]:+d}')
    print(f'购买率变化：{result["change"]["conversion_percentage_points"]:+.4f} 个百分点')
    if "diagnostics" in result:
        diag = result["diagnostics"]
        print("\n来源分解（单位：百分点）：")
        print(f'来源占比变化：{diag["source"]["mix_change_pp"]:+.6f}')
        print(f'来源内购买率变化：{diag["source"]["within_change_pp"]:+.6f}')
        print("按购买人数变化从小到大排列的前三个来源：")
        for row in diag["source"]["groups"][:3]:
            print(f'{row["source"]!r} / {row["medium"]!r}: {row["previous_buyers"]} → {row["current_buyers"]}（{row["buyer_change"]:+d}）')
        print(f'放宽时间筛选后的购买率变化：{diag["sensitivity"]["conversion_change_pp"]:+.4f} 个百分点')
        print("分组与总数核对通过。以上为算术分解，不代表已证明业务原因。")
    result["queried_at_utc"]=datetime.now(timezone.utc).isoformat()
    result["execution"]="live_mysql_query"
    folder=ROOT/"data"/"agent_runs";folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path=folder/f"compare_{args.week}_{stamp}.json"
    try:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    except OSError:
        print("数据库查询成功，但结果文件保存失败；请反馈目录写入问题。",file=sys.stderr);return 1
    print(f"结果已保存：{path}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
