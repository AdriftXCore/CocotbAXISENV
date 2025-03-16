module axis_test (
    input  logic                    clk         ,
    input  logic                    rst_n       ,
    input  logic [128       -1:0]   rx_meta_data,
    input  logic [16        -1:0]   rx_meta_keep,
    input  logic                    rx_meta_vld ,
    input  logic [  4       -1:0]   rx_meta_tid ,
    input  logic [  4       -1:0]   rx_meta_tdt ,
    input  logic                    rx_meta_sop ,
    input  logic                    rx_meta_eop ,
    output logic                    rx_meta_rdy ,              

    output logic [128       -1:0]   tx_meta_data,
    output logic [16        -1:0]   tx_meta_keep,
    output logic                    tx_meta_vld ,
    output logic [  4       -1:0]   tx_meta_tid ,
    output logic [  4       -1:0]   tx_meta_tdt ,
    output logic                    tx_meta_sop ,
    output logic                    tx_meta_eop ,
    input  logic                    tx_meta_rdy  
);

//Valid
always @(posedge clk or negedge rst_n)
    if (!rst_n)  
        tx_meta_vld <= 1'b0;
    else        
        tx_meta_vld <= rx_meta_rdy ? rx_meta_vld : tx_meta_vld;
//Data
always @(posedge clk or negedge rst_n)
    if (!rst_n)  
        {tx_meta_data,tx_meta_keep,tx_meta_tid,tx_meta_tdt,tx_meta_sop,tx_meta_eop} <= 'd0;
    else        
        {tx_meta_data,tx_meta_keep,tx_meta_tid,tx_meta_tdt,tx_meta_sop,tx_meta_eop} <= (rx_meta_rdy && rx_meta_vld) ? {rx_meta_data,rx_meta_keep,rx_meta_tid,rx_meta_tdt,rx_meta_sop,rx_meta_eop} : {tx_meta_data,tx_meta_keep,tx_meta_tid,tx_meta_tdt,tx_meta_sop,tx_meta_eop};
//READY with buble collapsing.
assign rx_meta_rdy = tx_meta_rdy || ~tx_meta_vld;

// assign tx_meta_data = rx_meta_data;
// assign tx_meta_keep = rx_meta_keep;
// assign tx_meta_vld  = rx_meta_vld ;
// assign tx_meta_tid  = rx_meta_tid ;
// assign tx_meta_tdt  = rx_meta_tdt ;
// assign tx_meta_sop  = rx_meta_sop ;
// assign tx_meta_eop  = rx_meta_eop ;
// assign rx_meta_rdy  = tx_meta_rdy ;

endmodule