RUNABLE = testRun.py

.PHONY: run clean view

run:
	python3 $(RUNABLE)

view:
	wslview parsedTree.gv.svg && wslview parsedAutomaton.gv.svg && wslview detAutomaton.gv.svg 

clean:
	rm -f *.gv *.gv.svg *.gv.pdf