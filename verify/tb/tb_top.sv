`timescale 1ns/1ns

module tb_top;

logic                    clk           ;
logic                    rst_n         ;
logic                    rst           ;
logic [128       -1:0]   s_axis_tdata  ;
logic [16        -1:0]   s_axis_tkeep  ;
logic                    s_axis_tvalid ;
logic [10        -1:0]   s_axis_tuser  ;
logic                    s_axis_tready ;              

logic [128       -1:0]   m_axis_tdata  ;
logic [16        -1:0]   m_axis_tkeep  ;
logic                    m_axis_tvalid ;
logic [10        -1:0]   m_axis_tuser  ;
logic                    m_axis_tready ;   

logic [128       -1:0]   rx_meta_data  ;
logic [16        -1:0]   rx_meta_keep  ;
logic                    rx_meta_vld   ;
logic [4         -1:0]   rx_meta_tid   ;
logic [4         -1:0]   rx_meta_tdt   ;
logic                    rx_meta_sop   ;
logic                    rx_meta_eop   ;
logic                    rx_meta_rdy   ;     

logic [128       -1:0]   tx_meta_data  ;
logic [16        -1:0]   tx_meta_keep  ;
logic                    tx_meta_vld   ;
logic [4         -1:0]   tx_meta_tid   ;
logic [4         -1:0]   tx_meta_tdt   ;
logic                    tx_meta_sop   ;
logic                    tx_meta_eop   ;
logic                    tx_meta_rdy   ;     

assign rx_meta_data = s_axis_tdata ;
assign rx_meta_keep = s_axis_tkeep ;
assign rx_meta_vld  = s_axis_tvalid;
assign {rx_meta_tid,rx_meta_tdt,rx_meta_sop,rx_meta_eop} = s_axis_tuser;
assign s_axis_tready = rx_meta_rdy;

assign m_axis_tdata  = tx_meta_data;
assign m_axis_tkeep  = tx_meta_keep;
assign m_axis_tvalid = tx_meta_vld ;
assign m_axis_tuser  = {tx_meta_tid,tx_meta_tdt,tx_meta_sop,tx_meta_eop};
assign tx_meta_rdy   = m_axis_tready;

assign rst = ~rst_n;

axis_test u_axis_test (
    .clk         (clk         ),
    .rst_n       (rst_n       ),
    .rx_meta_data(rx_meta_data),
    .rx_meta_keep(rx_meta_keep),
    .rx_meta_vld (rx_meta_vld ),
    .rx_meta_tid (rx_meta_tid ),
    .rx_meta_tdt (rx_meta_tdt ),
    .rx_meta_sop (rx_meta_sop ),
    .rx_meta_eop (rx_meta_eop ),
    .rx_meta_rdy (rx_meta_rdy ),              

    .tx_meta_data(tx_meta_data),
    .tx_meta_keep(tx_meta_keep),
    .tx_meta_vld (tx_meta_vld ),
    .tx_meta_tid (tx_meta_tid ),
    .tx_meta_tdt (tx_meta_tdt ),
    .tx_meta_sop (tx_meta_sop ),
    .tx_meta_eop (tx_meta_eop ),
    .tx_meta_rdy (tx_meta_rdy ) 
);


initial begin
    $fsdbDumpfile("tb_top.fsdb");
    $fsdbDumpvars(0, tb_top,"+all");
end


endmodule