module decoder (
  input  logic                  valid_i,
  input  logic [31:0]           instr_i,
  input  logic [31:0]           pc_i,
  output riscv_pkg::decoded_t   dec_o
);
  import riscv_pkg::*;

  logic [6:0] opcode;
  logic [2:0] funct3;
  logic [6:0] funct7;

  always_comb begin
    opcode = instr_i[6:0];
    funct3 = instr_i[14:12];
    funct7 = instr_i[31:25];

    dec_o = '0;
    dec_o.valid   = valid_i;
    dec_o.instr   = instr_i;
    dec_o.pc      = pc_i;
    dec_o.rs1     = instr_i[19:15];
    dec_o.rs2     = instr_i[24:20];
    dec_o.rd      = instr_i[11:7];
    dec_o.alu_op  = ALU_ADD;
    dec_o.branch_op = BR_NONE;
    dec_o.mdu_op  = MDU_NONE;
    dec_o.mem_size = MEM_W;
    dec_o.illegal = valid_i;

    if (!valid_i) begin
      dec_o.illegal = 1'b0;
    end else begin
      unique case (opcode)
        7'b0110111: begin // LUI
          dec_o.illegal = 1'b0;
          dec_o.rd_write = 1'b1;
          dec_o.imm = {instr_i[31:12], 12'b0};
          dec_o.use_imm = 1'b1;
          dec_o.op_a_zero = 1'b1;
          dec_o.alu_op = ALU_COPY_B;
          dec_o.lane1_eligible = 1'b1;
        end

        7'b0010111: begin // AUIPC
          dec_o.illegal = 1'b0;
          dec_o.rd_write = 1'b1;
          dec_o.imm = {instr_i[31:12], 12'b0};
          dec_o.use_imm = 1'b1;
          dec_o.op_a_pc = 1'b1;
          dec_o.alu_op = ALU_ADD;
          dec_o.lane1_eligible = 1'b1;
        end

        7'b1101111: begin // JAL
          dec_o.illegal = 1'b0;
          dec_o.rd_write = 1'b1;
          dec_o.is_jal = 1'b1;
          dec_o.imm = {{11{instr_i[31]}}, instr_i[31], instr_i[19:12], instr_i[20], instr_i[30:21], 1'b0};
        end

        7'b1100111: begin // JALR
          if (funct3 == 3'b000) begin
            dec_o.illegal = 1'b0;
            dec_o.rs1_used = 1'b1;
            dec_o.rd_write = 1'b1;
            dec_o.is_jalr = 1'b1;
            dec_o.imm = {{20{instr_i[31]}}, instr_i[31:20]};
          end
        end

        7'b1100011: begin // BRANCH
          dec_o.rs1_used = 1'b1;
          dec_o.rs2_used = 1'b1;
          dec_o.is_branch = 1'b1;
          dec_o.imm = {{19{instr_i[31]}}, instr_i[31], instr_i[7], instr_i[30:25], instr_i[11:8], 1'b0};
          unique case (funct3)
            3'b000: begin dec_o.illegal = 1'b0; dec_o.branch_op = BR_EQ;  end
            3'b001: begin dec_o.illegal = 1'b0; dec_o.branch_op = BR_NE;  end
            3'b100: begin dec_o.illegal = 1'b0; dec_o.branch_op = BR_LT;  end
            3'b101: begin dec_o.illegal = 1'b0; dec_o.branch_op = BR_GE;  end
            3'b110: begin dec_o.illegal = 1'b0; dec_o.branch_op = BR_LTU; end
            3'b111: begin dec_o.illegal = 1'b0; dec_o.branch_op = BR_GEU; end
            default: ;
          endcase
        end

        7'b0000011: begin // LOAD
          dec_o.rs1_used = 1'b1;
          dec_o.rd_write = 1'b1;
          dec_o.is_load = 1'b1;
          dec_o.use_imm = 1'b1;
          dec_o.imm = {{20{instr_i[31]}}, instr_i[31:20]};
          unique case (funct3)
            3'b000: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_B; dec_o.load_unsigned = 1'b0; end
            3'b001: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_H; dec_o.load_unsigned = 1'b0; end
            3'b010: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_W; dec_o.load_unsigned = 1'b0; end
            3'b100: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_B; dec_o.load_unsigned = 1'b1; end
            3'b101: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_H; dec_o.load_unsigned = 1'b1; end
            default: ;
          endcase
        end

        7'b0100011: begin // STORE
          dec_o.rs1_used = 1'b1;
          dec_o.rs2_used = 1'b1;
          dec_o.is_store = 1'b1;
          dec_o.use_imm = 1'b1;
          dec_o.imm = {{20{instr_i[31]}}, instr_i[31:25], instr_i[11:7]};
          unique case (funct3)
            3'b000: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_B; end
            3'b001: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_H; end
            3'b010: begin dec_o.illegal = 1'b0; dec_o.mem_size = MEM_W; end
            default: ;
          endcase
        end

        7'b0010011: begin // OP-IMM
          dec_o.rs1_used = 1'b1;
          dec_o.rd_write = 1'b1;
          dec_o.use_imm = 1'b1;
          dec_o.imm = {{20{instr_i[31]}}, instr_i[31:20]};
          dec_o.lane1_eligible = 1'b1;
          unique case (funct3)
            3'b000: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_ADD;  end // ADDI
            3'b010: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SLT;  end
            3'b011: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SLTU; end
            3'b100: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_XOR;  end
            3'b110: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_OR;   end
            3'b111: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_AND;  end
            3'b001: begin
              if (funct7 == 7'b0000000) begin
                dec_o.illegal = 1'b0;
                dec_o.alu_op = ALU_SLL;
                dec_o.imm = {27'd0, instr_i[24:20]};
              end
            end
            3'b101: begin
              if (funct7 == 7'b0000000) begin
                dec_o.illegal = 1'b0;
                dec_o.alu_op = ALU_SRL;
                dec_o.imm = {27'd0, instr_i[24:20]};
              end else if (funct7 == 7'b0100000) begin
                dec_o.illegal = 1'b0;
                dec_o.alu_op = ALU_SRA;
                dec_o.imm = {27'd0, instr_i[24:20]};
              end
            end
            default: ;
          endcase
          if (dec_o.illegal)
            dec_o.lane1_eligible = 1'b0;
        end

        7'b0110011: begin // OP / M
          dec_o.rs1_used = 1'b1;
          dec_o.rs2_used = 1'b1;
          dec_o.rd_write = 1'b1;
          if (funct7 == 7'b0000001) begin
            unique case (funct3)
              3'b000: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_MUL;    end
              3'b001: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_MULH;   end
              3'b010: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_MULHSU; end
              3'b011: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_MULHU;  end
              3'b100: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_DIV;    end
              3'b101: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_DIVU;   end
              3'b110: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_REM;    end
              3'b111: begin dec_o.illegal = 1'b0; dec_o.mdu_op = MDU_REMU;   end
              default: ;
            endcase
          end else begin
            unique case ({funct7, funct3})
              {7'b0000000,3'b000}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_ADD;  end
              {7'b0100000,3'b000}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SUB;  end
              {7'b0000000,3'b001}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SLL;  end
              {7'b0000000,3'b010}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SLT;  end
              {7'b0000000,3'b011}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SLTU; end
              {7'b0000000,3'b100}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_XOR;  end
              {7'b0000000,3'b101}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SRL;  end
              {7'b0100000,3'b101}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_SRA;  end
              {7'b0000000,3'b110}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_OR;   end
              {7'b0000000,3'b111}: begin dec_o.illegal = 1'b0; dec_o.alu_op = ALU_AND;  end
              default: ;
            endcase
            if (!dec_o.illegal)
              dec_o.lane1_eligible = 1'b1;
          end
        end

        7'b1110011: begin // SYSTEM: ECALL / EBREAK only
          dec_o.is_system = 1'b1;
          if (instr_i == 32'h0000_0073) begin
            dec_o.illegal = 1'b0;
            dec_o.is_ecall = 1'b1;
          end else if (instr_i == 32'h0010_0073) begin
            dec_o.illegal = 1'b0;
            dec_o.is_ebreak = 1'b1;
          end
        end

        default: ;
      endcase
    end
  end
endmodule
