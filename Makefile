RUNABLE = testRun.py

.PHONY: run clean view

run:
	python3 $(RUNABLE)

view: parsedTree.gv.pdf parsedAutomaton.gv.pdf
	wslview parsedTree.gv.pdf && wslview parsedAutomaton.gv.pdf

clean:
	rm -f *.gv *.gv.pdf