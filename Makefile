RUNABLE = testRun.py

.PHONY: run clean view

run:
	python3 $(RUNABLE)

view:
	wslview parsedTree.gv.svg && wslview parsedAutomaton.gv.pdf && wslview detAutomaton.gv.pdf 

clean:
	rm -f *.gv *.gv.svg *.gv.pdf