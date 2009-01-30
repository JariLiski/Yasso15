.. -yasso-py:

########
yasso.py
########

Classes for running the Yasso model. Contais three different sets of classes.

1) Base data classes for Yasso (LitterComponent, TimelitterComponent, ConstantClimate, MonthlyClimate and YearlyClimate)

2) Table editor instances for the Yasso UI data grids: monthly_climate_te, yearly_climate_te, litter_component_te, timed_litter_component_te, c_stock_te and co2_yield. Associated with the last two are two tabular adapter classes: CStockAdapter and CO2YieldAdapter

3) The actual Yasso class that uses the previous two, to define the data model used by the program, the UI components, and the event handlers that wire the data model, UI components, and the actual yasso model together.

The model is run by the ModelRunner class (see separate document).

***********************
class Yasso(HasTraits):
***********************

Contains the data model, the UI definition and the event handlers::
    

