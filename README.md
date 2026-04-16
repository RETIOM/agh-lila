# LILA - Light Intermediate Language Architecture
- Tomasz Idźkowski - idzkowskit@student.agh.edu.pl
- Maksymilian Koleśniak - mkolesniak@student.agh.edu.pl

## Temat
Kompilator dla języka proceduralnego wykorzystującego składnię hybrydową opartą na C/Rust/Zig do reprezentacji LLVM.

## Opis
### Ogólne cele
Głównym celem projektu jest zaprojektowanie oraz implementacja kompilatora dla autorskiego języka programowania do LLVM. 
### Rodzaj translatora
Kompilator - program tłumaczy kod źródłowy napisany we własnym języku na kod LLVM IR.
### Planowany wynik działania programu
Kompialtor języka do kodu LLVM IR w formacie tekstowym `.ll`. Wygenerowany kod możę być następnie przetwarzany przez narzędzia LLVM.

## Język implementacji
`Python 3.14`

## Generator parserów
`PLY`
