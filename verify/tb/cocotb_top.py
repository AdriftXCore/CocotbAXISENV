'''
Author:zhanghx(https://github.com/AdriftXCore)
date:2025-03-01 23:02:10
'''
import random
import cocotb
# from cocotb.triggers import RisingEdge, Timer, Event
from cocotb.triggers import *
from cocotbext.axi import AxiStreamBus, AxiStreamSource, AxiStreamSink, AxiStreamFrame

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


@cocotb.test()
async def dff_simple_test(dut):
    # clock
    await cocotb.start(generate_clock(dut,20,"us",0))

    reset_task = cocotb.start_soon(reset_logic(dut,False,10))
    
    # Set initial input value to prevent it from floating
    '''
    tdata：数据，必需
    tvalid：限定所有其他信号；可选，缺省时假设为1
    tready：指示接收端准备好接收数据；可选，缺省时假设为1
    tlast：标记帧的最后一个周期；可选，缺省时假设为1
    tkeep：限定数据字节，数据总线宽度必须能被tkeep信号宽度整除；可选，缺省时假设为1
    tid：ID信号，可用于路由；可选，缺省时假设为0
    tdest：目标信号，可用于路由；可选，缺省时假设为0
    tuser：附加用户数据；可选，缺省时假设为0
    '''
    dut.s_axis_tdata.value = 0  
    dut.s_axis_tkeep.value = 0  
    dut.s_axis_tvalid.value = 0  
    dut.s_axis_tuser.value = 0
    dut.m_axis_tready.value = 1

    #reset
    await reset_task

    '''
    bus：包含AXI流接口信号的AxiStreamBus对象
    clock：时钟信号
    reset：复位信号（可选）
    reset_active_level：复位激活级别（可选，默认为True，高有效）
    byte_size：字节大小（可选）
    byte_lanes：字节通道数（可选）
    注意：byte_size、byte_lanes、len(tdata)和len(tkeep)都有关联，
    即byte_lanes如果连接，则从tkeep设置，并且byte_size*byte_lanes == len(tdata)。
    因此，如果tkeep连接，则byte_size和byte_lanes都将在内部计算，并且不能被覆盖。
    如果tkeep未连接，则可以指定byte_size或byte_lanes，
    另一个将被计算，使得byte_size*byte_lanes == len(tdata)。
    '''
    axis_source = AxiStreamSource(
        AxiStreamBus.from_prefix(dut, "s_axis"),
        dut.clk,
        dut.rst_n, #可选
        reset_active_level=False #可选
        # byte_size=8,  
        # byte_lanes=16
    )
    axis_sink = AxiStreamSink(
        AxiStreamBus.from_prefix(dut, "m_axis"),
        dut.clk,
        dut.rst_n, #可选
        reset_active_level=False
    )

    # 发送数据
    '''
    send(frame): 发送帧（阻塞）（源）
    send_nowait(frame): 发送帧（非阻塞）（源）
    write(data): 发送数据（send的别名）（阻塞）（源）
    write_nowait(data): 发送数据（send_nowait的别名）（非阻塞）（源）
    recv(compact=True): 接收一个帧作为GmiiFrame（阻塞）（接收端）
    recv_nowait(compact=True): 接收一个帧作为GmiiFrame（非阻塞）（接收端）
    read(count): 从缓冲区读取 count 个字节（阻塞）（接收端/监控）
    read_nowait(count): 从缓冲区读取 count 个字节（非阻塞）（接收端/监控）
    count(): 返回队列中的项数（所有）
    empty(): 如果队列为空则返回 True（所有）
    full(): 如果队列占用限制被满足则返回 True（源/接收端）
    idle(): 如果没有传输正在进行或队列不为空则返回 True（所有）或（源）
    clear(): 丢弃队列中的所有数据（所有）
    wait(): 等待空闲（源）
    wait(timeout=0, timeout_unit='ns'): 等待帧被接收（接收端）
    set_pause_generator(generator): 设置暂停信号的生成器，生成器将在每个时钟周期被推进（源/接收端）
    clear_pause_generator(): 删除暂停信号的生成器（源/接收端）
    '''
    await axis_source.send(b'Hello, AXIS!')
    dut._log.info(f"SEND DATA FOR TEST")
    dut._log.info(f"s_axis_tready is :{dut.s_axis_tready.value}")
    # 接收并验证数据
    received_frame = await axis_sink.recv()
    dut._log.info(f"recieve data :{received_frame}")
    assert received_frame.tdata == b'Hello, AXIS!', "Data mismatch"

    await RisingEdge(dut.clk)
    # 创建帧（支持自定义 tlast、tuser 等）
    '''
    tdata：字节、字节数组或列表
    tkeep：tkeep字段， 可选；列表，每个条目限定相应的tdata条目。可以用来在源端插入间隙。
    tid：tid字段， 可选；整数或与tdata每个条目对应的列表，每个发送周期使用最后一个值。
    tdest：tdest字段， 可选；整数或与tdata每个条目对应的列表，每个发送周期使用最后一个值。
    tuser：tuser字段， 可选；整数或与tdata每个条目对应的列表，每个发送周期使用最后一个值。
    sim_time_start：帧的第一个传输周期的模拟时间。
    sim_time_end：帧的最后一个传输周期的模拟时间。
    tx_complete：帧传输完成时触发的事件或可调用函数。
    '''
    frame = AxiStreamFrame(
        tdata=b'test_data', 
        tuser=0x3, 
        tx_complete=Event()  # 传输完成事件
    )
    await axis_source.send(frame)
    dut._log.info(f"SEND DATA FOR FRAME TEST")
    await frame.tx_complete.wait()
    dut._log.info(f"Frame sent at {frame.tx_complete.data.sim_time_start} ns")

    # 可选：等待若干周期后结束
    for _ in range(10):
        await RisingEdge(dut.clk)
