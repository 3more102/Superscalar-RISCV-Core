package riscv_pkg;
  parameter int XLEN = 32;

  typedef enum logic [4:0] {
    ALU_ADD, ALU_SUB, ALU_SLL, ALU_SLT, ALU_SLTU,
    ALU_XOR, ALU_SRL, ALU_SRA, ALU_OR, ALU_AND,
    ALU_COPY_B
  } alu_op_e;

  typedef enum logic [2:0] {
    BR_NONE, BR_EQ, BR_NE, BR_LT, BR_GE, BR_LTU, BR_GEU
  } branch_op_e;

  typedef enum logic [3:0] {
    MDU_NONE,
    MDU_MUL, MDU_MULH, MDU_MULHSU, MDU_MULHU,
    MDU_DIV, MDU_DIVU, MDU_REM, MDU_REMU
  } mdu_op_e;

  typedef enum logic [1:0] {
    MEM_B, MEM_H, MEM_W
  } mem_size_e;

  typedef struct packed {
    logic        valid;
    logic [31:0] instr;
    logic [31:0] pc;

    logic [4:0]  rs1;
    logic [4:0]  rs2;
    logic [4:0]  rd;
    logic        rs1_used;
    logic        rs2_used;
    logic        rd_write;

    logic [31:0] imm;
    logic        use_imm;
    logic        op_a_pc;
    logic        op_a_zero;

    alu_op_e     alu_op;
    branch_op_e  branch_op;
    mdu_op_e     mdu_op;

    logic        is_branch;
    logic        is_jal;
    logic        is_jalr;
    logic        is_load;
    logic        is_store;
    logic        is_system;
    logic        is_ecall;
    logic        is_ebreak;
    logic        illegal;

    mem_size_e   mem_size;
    logic        load_unsigned;

    logic        lane1_eligible;
  } decoded_t;

  typedef struct packed {
    logic        valid;
    decoded_t    dec;
    logic [31:0] op1;
    logic [31:0] op2;
    logic [31:0] store_data;
  } ex_pipe_t;

  typedef struct packed {
    logic        valid;
    decoded_t    dec;
    logic [31:0] result;
    logic [31:0] mem_addr;
    logic [31:0] store_data;
    logic        exc_valid;
    logic [3:0]  exc_cause;
  } mem_pipe_t;

  typedef struct packed {
    logic        valid;
    decoded_t    dec;
    logic [31:0] wb_value;
    logic [31:0] mem_addr;
    logic [31:0] store_data;
    logic        mem_write;
    logic        exc_valid;
    logic [3:0]  exc_cause;
  } wb_pipe_t;

  localparam logic [3:0] EXC_INSTR_MISALIGNED = 4'd0;
  localparam logic [3:0] EXC_ILLEGAL          = 4'd2;
  localparam logic [3:0] EXC_BREAKPOINT       = 4'd3;
  localparam logic [3:0] EXC_LOAD_MISALIGNED  = 4'd4;
  localparam logic [3:0] EXC_STORE_MISALIGNED = 4'd6;
  localparam logic [3:0] EXC_ECALL_M          = 4'd11;

endpackage
