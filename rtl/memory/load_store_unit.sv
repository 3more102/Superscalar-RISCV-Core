module load_store_unit (
  input  riscv_pkg::decoded_t dec,
  input  logic [31:0]         eff_addr,
  input  logic [31:0]         store_data_raw,
  input  logic [31:0]         dmem_rdata,
  output logic [31:0]         aligned_addr,
  output logic [31:0]         store_wdata,
  output logic [3:0]          store_be,
  output logic [31:0]         load_value
);
  import riscv_pkg::*;

  logic [31:0] shifted;
  logic [7:0]  byte_v;
  logic [15:0] half_v;

  always_comb begin
    aligned_addr = {eff_addr[31:2], 2'b00};
    shifted = dmem_rdata >> (8 * eff_addr[1:0]);
    byte_v = shifted[7:0];
    half_v = shifted[15:0];

    store_wdata = 32'd0;
    store_be = 4'b0000;
    load_value = 32'd0;

    unique case (dec.mem_size)
      MEM_B: begin
        store_wdata = store_data_raw << (8 * eff_addr[1:0]);
        store_be = 4'b0001 << eff_addr[1:0];
        load_value = dec.load_unsigned ? {24'd0, byte_v} : {{24{byte_v[7]}}, byte_v};
      end
      MEM_H: begin
        store_wdata = store_data_raw << (16 * eff_addr[1]);
        store_be = 4'b0011 << (2 * eff_addr[1]);
        load_value = dec.load_unsigned ? {16'd0, half_v} : {{16{half_v[15]}}, half_v};
      end
      MEM_W: begin
        store_wdata = store_data_raw;
        store_be = 4'b1111;
        load_value = dmem_rdata;
      end
      default: begin
      end
    endcase
  end
endmodule
