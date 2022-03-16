program vk;
var A:array[1..20] of integer;
N, i:integer;
Begin 

for i:=1 to 20 do
begin
A[i] := random(100) - 50;
write(A[i], ' ');
end;
writeln('');
writeln('Enter N:');
readln(N);
if (N > 0) and (N < 21) then
writeln('A[N-1] = ', A[N-1], '; A[N] = ', A[N], '; A[N+1] = ', A[N+1] );
end.
