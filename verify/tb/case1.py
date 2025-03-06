'''
Author:zhanghx(https://github.com/AdriftXCore)
date:2025-03-01 23:02:10
'''
import random
import cocotb
# from cocotb.triggers import RisingEdge, Timer, Event
from cocotb.triggers import *
from cocotbext.axi import AxiStreamBus, AxiStreamSource, AxiStreamSink, AxiStreamFrame
from collections import deque
from cocotb.queue import Queue
from cocotb.result import TestFailure  # 正确导入方式


async def generate_clock(dut, cycle, u, n):
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

async def reset_logic(dut, sync=True, cycles=1):
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
tx_queue = deque()
rx_queue = Queue()

async def continuous_sender(dut, source, frame_count=100):
    """背靠背帧发送协程"""
    try:
        for i in range(frame_count):
            frame = AxiStreamFrame(i.to_bytes(16,"little"))
            source.send_nowait(frame)  # 非阻塞发送
            await source.wait()
    except Exception as e:
        dut._log.error(f"Sender failed: {e}")
        raise

def random_backpressure():
    """生成随机反压信号（30%概率触发）"""
    while True:
        yield random.random() < 0.3  # 30%概率拉低tready

async def apply_backpressure(dut, sink):
    try:
        """反压控制协程"""
        sink.set_pause_generator(random_backpressure())
    except Exception as e:
        dut._log.error(f"backpresse failed: {e}")
        raise



async def data_validator(dut, sink):
    """独立校验协程"""
    frame = await sink.recv_nowait()
    assert frame.tdata == b'0', "CHECK ERROR"
    dut._log.info("CHECK PASS")

@cocotb.test()
async def dff_simple_test(dut):
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
    backpressure = cocotb.start_soon(apply_backpressure(dut, axis_sink))
    dut._log.info("------------------ initial backpressure ------------------")
    sender = cocotb.start_soon(continuous_sender(dut, axis_source, 100))
    dut._log.info("------------------ initial sender ------------------")


    # validator = cocotb.start_soon(data_validator(dut, axis_sink))

    frame = await axis_sink.recv()

    # assert frame.tdata == b'0', "CHECK ERROR"
    dut._log.info(f"the frame data is {frame.tdata}")
    # 等待所有任务完成
    # await sender
    # await Combine(sender, validator)
    # await validator
    dut._log.info("TEST COMPLETE")
    sender.kill()
    for _ in range(10):
        await RisingEdge(dut.clk)
        dut._log.info("done")


