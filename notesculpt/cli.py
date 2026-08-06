import time
import click
from pathlib import Path
from notesculpt.config import ConfigLoader
from notesculpt.llm import LLMClient
from notesculpt.refiner import Refiner
from notesculpt.files import discover_files, read_file, output_path, write_file, load_prompt_file
from notesculpt.models import RefineRequest, RefineResult


@click.group()
def cli():
    """NoteSculpt — 智能笔记精炼器"""


@cli.command()
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--level",
    type=click.Choice(["brief", "moderate", "detailed"]),
    default="moderate",
    help="精炼程度",
)
@click.option(
    "--prompt-file",
    type=click.Path(exists=True, path_type=Path),
    help="自定义精炼指令文件",
)
@click.option("--in-place", is_flag=True, help="原地覆盖原文件")
@click.option("--stdout", is_flag=True, help="输出到标准输出")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="指定输出目录",
)
def refine(target, level, prompt_file, in_place, stdout, output_dir):
    """精炼 Markdown 笔记"""
    if in_place and stdout:
        raise click.UsageError("--in-place 和 --stdout 不能同时使用")
    if in_place and output_dir:
        raise click.UsageError("--in-place 和 --output-dir 不能同时使用")

    if in_place:
        click.confirm("⚠ 原地覆盖模式将直接修改原文件，是否继续？", abort=True)

    config = ConfigLoader().load()
    llm = LLMClient(config)
    refiner = Refiner(llm)

    custom_prompt = load_prompt_file(prompt_file) if prompt_file else None
    files = discover_files(target)
    results = []
    failures = []
    start_time = time.time()

    for file_path in files:
        try:
            content = read_file(file_path)
            request = RefineRequest(
                content=content,
                file_path=file_path,
                level=level,
                custom_prompt=custom_prompt,
            )
            result = refiner.refine(request)
            results.append(result)

            output = format_output(result)
            if stdout:
                click.echo(output)
            elif in_place:
                write_file(file_path, output)
            else:
                out = output_path(file_path, output_dir)
                write_file(out, output)
                click.echo(f"✓ {file_path.name} → {out.name}")
        except Exception as e:
            failures.append((file_path, str(e)))
            click.echo(f"✗ {file_path.name}: {e}", err=True)
            if len(files) == 1:
                raise

    if len(files) > 1:
        elapsed = time.time() - start_time
        click.echo()
        click.echo("📊 批量处理完成")
        click.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        click.echo(f"成功：{len(results)}/{len(files)} 个文件")
        click.echo(f"失败：{len(failures)}/{len(files)} 个文件")
        if failures:
            click.echo("失败文件：")
            for path, error in failures:
                click.echo(f"  - {path}：{error}")
        click.echo(f"处理耗时：{elapsed:.1f}s")


@cli.group()
def config():
    """管理 API Key 配置"""


@config.command("set-key")
def set_key():
    """将 API Key 存入系统 keyring"""
    api_key = click.prompt("请输入 DeepSeek API Key", hide_input=True)
    loader = ConfigLoader()
    loader.set_key(api_key)
    click.echo("✓ API Key 已存入 keyring")


@config.command("delete-key")
def delete_key():
    """从 keyring 中删除 API Key"""
    loader = ConfigLoader()
    loader.delete_key()
    click.echo("✓ API Key 已从 keyring 删除")


@config.command("show-status")
def show_status():
    """显示当前配置状态"""
    loader = ConfigLoader()
    status = loader.get_status()
    click.echo(f"API Key 已配置: {'是' if status['key_configured'] else '否'}")
    click.echo(f"模型: {status['model']}")
    click.echo(f"API 地址: {status['base_url']}")


def format_output(result: RefineResult) -> str:
    if result.original_chars > 0:
        ratio = (1 - result.refined_chars / result.original_chars) * 100
    else:
        ratio = 0.0
    return f"""> 📝 **精炼信息**
> - 精炼时间：{result.timestamp:%Y-%m-%d %H:%M:%S}
> - 原始字数：{result.original_chars:,} 字 → 精炼后：{result.refined_chars:,} 字
> - 精炼级别：{result.level}
> - 压缩比：{ratio:.0f}%

{result.refined_content}"""