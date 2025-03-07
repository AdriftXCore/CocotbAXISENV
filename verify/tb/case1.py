'''
Author:zhanghx(https://github.com/AdriftXCore)
date:2025-03-01 23:02:10
'''
import random
import cocotb
from cocotb.handle import SimHandle
from typing import Generator
from cocotb.triggers import *
from cocotbext.axi import AxiStreamBus, AxiStreamSource, AxiStreamSink, AxiStreamFrame
from collections import deque
from cocotb.queue import Queue



async def generate_clock(dut: SimHandle, cycle: int, u: int, n: int) -> None:
    """Generate clock pulses."""
    if(n == 0):
        while True:
            dut.clk.value = 0
            await Timer(cycle/2, units=u)
            dut.clk.value = 1
            await Timer(cycle/2, units=u)
    else:
        for i in range(n):
            dut.clk.value = 0
            await Timer(cycle/2, units=u)
            dut.clk.value = 1
            await Timer(cycle/2, units=u)

async def reset_logic(dut: SimHandle, sync: bool, cycles: int) -> None:
    """支持同步/异步复位的控制函数
    :param sync: True为同步复位（依赖时钟），False为异步复位
    :param cycles: 同步复位时的时钟周期数
    """
    if sync:
        await RisingEdge(dut.clk)  # 对齐时钟边沿
        dut.rst_n.value = 0
        for _ in range(cycles):
            await RisingEdge(dut.clk)
        dut.rst_n.value = 1
    else:
        dut.rst_n.value = 1
        await Timer(1, units="ns")
        dut.rst_n.value = 0
        await Timer(100, units="ns")  # 异步复位无需时钟同步
        dut.rst_n.value = 1

# 初始化发送队列和反压状态
rx_queue = Queue()

async def continuous_sender(dut: SimHandle, source: AxiStreamSource, frame_count: int) -> None:
    """背靠背帧发送协程"""
    try:
        for i in range(frame_count):
            frame = AxiStreamFrame(i.to_bytes(16,"little"))
            source.send_nowait(frame)  # 非阻塞发送
            await source.wait()
    except Exception as e:
        dut._log.error(f"Sender failed: {e}")
        raise

def random_backpressure(n: float,seed: int) -> Generator[bool, None, None]:
    """生成随机反压信号（30%概率触发）"""
    random.seed(seed)  # 设置种子值
    while True:
        yield random.random() < n  # 30%概率拉低tready

async def apply_backpressure(dut: SimHandle, sink: AxiStreamSink,n: float,seek :int):
    try:
        """反压控制协程"""
        sink.set_pause_generator(random_backpressure(n,seek))
    except Exception as e:
        dut._log.error(f"backpresse failed: {e}")
        raise

async def receiver_monitor(dut: SimHandle, sink: AxiStreamSink):
    try:
        """异步接收协程"""
        while True:
            frame = await sink.recv()  # 阻塞式接收
            rx_queue.put_nowait(frame)  # 非阻塞入队
    except Exception as e:
        dut._log.error(f"receiver failed: {e}")
        raise

errors = []
async def data_validator(dut: SimHandle, frame_count: int):
    result = 0
    while(result < frame_count):
        frame = await rx_queue.get()  # 阻塞式出队
        data = (int.from_bytes(frame.tdata, byteorder='little'))
        if data != result:
            errors.append(f"CHECK ERROR, got {data},the result is {hex(result)}")
            dut._log.error(f"verilate fail :{data},the result is {hex(result)}")
        else:
            dut._log.info(f"CHECK PASS receive data is :{data}")
        result = result + 1

@cocotb.test()
async def axis_simple_test(dut: SimHandle):
    # clock
    await cocotb.start(generate_clock(dut,20,"us",0))

    reset_task = cocotb.start_soon(reset_logic(dut,False,10))
    # Set initial input value to prevent it from floating
    dut.s_axis_tdata.value = 0  
    dut.s_axis_tkeep.value = 0  
    dut.s_axis_tvalid.value = 0  
    dut.s_axis_tuser.value = 0
    dut.m_axis_tready.value = 1
    #reset
    await reset_task

    # 创建 AXI Stream 接口对象
    axis_source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "s_axis"), dut.clk)
    axis_sink = AxiStreamSink(AxiStreamBus.from_prefix(dut, "m_axis"), dut.clk)

    dut._log.info("------------------ initial cfg ------------------")
    # 启动协程
    backpressure = cocotb.start_soon(apply_backpressure(dut, axis_sink, 0.3, 44))
    dut._log.info("------------------ initial backpressure ------------------")
    sender = cocotb.start_soon(continuous_sender(dut, axis_source, 100))
    dut._log.info("------------------ initial sender ------------------")
    monitor = cocotb.start_soon(receiver_monitor(dut, axis_sink))
    dut._log.info("------------------ initial monitor ------------------")
    validator = cocotb.start_soon(data_validator(dut, 100))
    dut._log.info("------------------ initial validator ------------------")

    await Combine(sender, validator)
    dut._log.info("------------------ sender complete------------------")

    await RisingEdge(dut.clk)
    assert len(errors) == 0,"TEST FAIL"
    dut._log.info("------------------ TEST COMPLETE ------------------")
    backpressure.kill()
    sender.kill()
    monitor.kill()
    validator.kill()
    for _ in range(10):
        await RisingEdge(dut.clk)
    dut._log.info("------------------ SIMULATE DONE ------------------")
