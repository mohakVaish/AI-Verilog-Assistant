module TwoBitAdder_tb;

  // Inputs
  reg [1:0] A;
  reg [1:0] B;

  // Outputs
  wire [2:0] SUM;

  // Clock and Reset (assuming they exist in the design)
  reg clk;
  reg rst;

  // Instantiate the Unit Under Test (DUT)
  TwoBitAdder dut (
    .A(A),
    .B(B),
    .SUM(SUM)
  );

  // Clock generation
  always #5 clk = ~clk;

  // Reset generation
  initial begin
    clk = 0;
    rst = 1;
    #10 rst = 0;
  end

  // Test vectors
  initial begin
    // Test vector 1
    A = 2'b00; B = 2'b00; #10; $display("Test 1: A=%b, B=%b, SUM=%b", A, B, SUM);
    // Test vector 2
    A = 2'b01; B = 2'b01; #10; $display("Test 2: A=%b, B=%b, SUM=%b", A, B, SUM);
    // Test vector 3
    A = 2'b10; B = 2'b10; #10; $display("Test 3: A=%b, B=%b, SUM=%b", A, B, SUM);
    // Test vector 4
    A = 2'b01; B = 2'b10; #10; $display("Test 4: A=%b, B=%b, SUM=%b", A, B, SUM);
    // Test vector 5
    A = 2'b11; B = 2'b11; #10; $display("Test 5: A=%b, B=%b, SUM=%b", A, B, SUM);

    $finish;
  end

endmodule


// Dummy module for testing (Replace with your actual TwoBitAdder module)
module TwoBitAdder (
  input [1:0] A,
  input [1:0] B,
  output [2:0] SUM
);
  assign SUM = A + B;
endmodule