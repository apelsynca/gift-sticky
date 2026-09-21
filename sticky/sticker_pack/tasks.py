from litestar_queues import task


@task("sticker_pack.update", timeout=30)
async def update_sticker_pack() -> str:
    print("Updating sticker pack")
    return "Some result of the update"
